import { Application } from "@hotwired/stimulus";
import ImageInputController from "./image_input_controller";
import WorkspaceController from "./workspace_controller";

const application = Application.start();
application.register("image-input", ImageInputController);
application.register("workspace", WorkspaceController);
