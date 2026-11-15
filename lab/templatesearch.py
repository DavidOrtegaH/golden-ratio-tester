"""Search fragmented edges without requiring a connected spiral contour."""
import math
import cv2
import numpy as np
from scipy.ndimage import map_coordinates
from scipy.optimize import least_squares
from .geometry import Candidate, GROWTH
from .contours import supported, duplicate


def edge_spirals(rgb, existing=()):
    scale = min(1, 640 / max(rgb.shape[:2]))
    rgb = cv2.resize(rgb, None, fx=scale, fy=scale) if scale < 1 else rgb
    gray = cv2.GaussianBlur(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY), (0, 0), 1.4)
    edges = cv2.Canny(gray, 40, 110)
    if np.count_nonzero(edges) < 100:
        return []
    h, w = gray.shape
    distance = cv2.distanceTransform(255 - edges, cv2.DIST_L2, 3)
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1)
    _, labels = cv2.distanceTransformWithLabels(255-edges, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    ys,xs=np.where(edges)
    lookup_x=np.zeros(len(xs)+1,np.float32);lookup_y=np.zeros(len(xs)+1,np.float32)
    lookup_x[labels[ys,xs]]=gx[ys,xs];lookup_y[labels[ys,xs]]=gy[ys,xs]
    nearest_x,nearest_y=lookup_x[labels],lookup_y[labels]
    t = np.linspace(-2 * math.pi, 0, 100)
    cx, cy, radius, phase = np.meshgrid(np.linspace(.15*w, .85*w, 9),
        np.linspace(.15*h, .85*h, 9), np.geomspace(max(60, min(h,w)*.2), max(h,w)*.85, 7),
        np.linspace(0, 2*math.pi, 24, endpoint=False), indexing='ij')
    poses = np.column_stack((cx.ravel(), cy.ravel(), np.log(radius.ravel()), phase.ravel()))
    proposals = []
    for sign in (-1, 1):
        for offset in range(0, len(poses), 2048):
            batch = poses[offset:offset+2048]
            angle = sign*t + batch[:, 3, None]
            r = np.exp(batch[:, 2, None] + GROWTH*t)
            x = batch[:, 0, None] + r*np.cos(angle)
            y = batch[:, 1, None] + r*np.sin(angle)
            ix, iy = np.rint(x).astype(int), np.rint(y).astype(int)
            valid = (ix>=0)&(ix<w)&(iy>=0)&(iy<h)
            ix,iy=np.clip(ix,0,w-1),np.clip(iy,0,h-1)
            # Tangent angle of the logarithmic spiral, compared to edge normal.
            tx = GROWTH*np.cos(angle)-sign*np.sin(angle)
            ty = GROWTH*np.sin(angle)+sign*np.cos(angle)
            norm = np.hypot(nearest_x[iy,ix],nearest_y[iy,ix])
            alignment = np.abs(tx*nearest_x[iy,ix]+ty*nearest_y[iy,ix])/np.maximum(np.hypot(tx,ty)*norm,1e-5)
            hits = valid & (distance[iy,ix]<max(h,w)*.025) & (alignment<.55) & (norm>8)
            scores=hits.mean(axis=1)
            for index in np.argsort(scores)[-4:]:
                if scores[index]>.35 and valid[index].mean()>.98:
                    proposals.append((float(scores[index]),sign,batch[index]))
    found=[]
    for _, sign, pose in sorted(proposals,key=lambda x:-x[0])[:48]:
        def curve(params):
            angle=sign*t+params[3]
            r=np.exp(params[2]+params[4]*t)
            return np.column_stack((params[0]+r*np.cos(angle),params[1]+r*np.sin(angle)))

        def residual(params):
            points=curve(params)
            return map_coordinates(distance,[points[:,1],points[:,0]],order=1,mode='constant',cval=30)

        initial=[*pose,GROWTH]
        fit=least_squares(residual,initial,
            bounds=([pose[0]-w/8,pose[1]-h/8,pose[2]-.25,pose[3]-.4,.1],
                    [pose[0]+w/8,pose[1]+h/8,pose[2]+.25,pose[3]+.4,.55]),
            diff_step=.001,max_nfev=60,loss='soft_l1',f_scale=2)
        if abs(fit.x[4]/GROWTH-1)>.08:
            continue
        golden=fit.x.copy();golden[4]=GROWTH
        points=curve(golden)
        error=np.sqrt(np.mean(residual(golden)**2))/np.linalg.norm(np.ptp(points,axis=0))
        if error>.012:
            continue
        candidate=Candidate('spiral',points.tolist(),float(error*100),
                            growth=math.exp(fit.x[4]*math.pi/2), metric='edge_distance',
                            model=(golden[0],golden[1],sign*GROWTH,golden[2]-sign*GROWTH*golden[3]))
        if supported(candidate,gray,edges):
            candidate.points=(points/scale).tolist()
            x,y,b,a=candidate.model
            candidate.model=(x/scale,y/scale,b,a-math.log(scale))
            if not duplicate(candidate,[*existing,*found]):
                found.append(candidate)
    return found[:6]
