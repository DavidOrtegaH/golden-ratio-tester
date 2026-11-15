import { Application } from "@hotwired/stimulus";
import ImageInputController from "./image_input_controller";

const application = Application.start();
application.register("image-input", ImageInputController);
