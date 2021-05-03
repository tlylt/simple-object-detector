from PIL import Image
import numpy as np
import flask
import io
import cv2
import os.path
from flask import send_file
from flask import render_template
import time
import base64

# Load names of classes from coco
classes = open('./YOLOv3/coco.names').read().strip().split('\n')

# initialize our Flask application
app = flask.Flask(__name__)
model = None
app.static_folder = 'static'


def getOutputsNames(net):  # Get the names of the output layers
    layersNames = net.getLayerNames()
    return [layersNames[i[0] - 1] for i in net.getUnconnectedOutLayers()]


def drawPred(image, classId, conf, left, top, right, bottom):  # Draw predicted bounding box
    cv2.rectangle(image, (left, top), (right, bottom), (255, 178, 50), 3)

    label = '%.2f' % conf
    assert(classId < len(classes))
    label = '%s:%s' % (classes[classId], label)

    # Display the label at the top of the bounding box
    labelSize, baseLine = cv2.getTextSize(
        label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    top = max(top, labelSize[1])
    cv2.rectangle(image, (left, top - round(1.5*labelSize[1])), (left + round(
        1.5*labelSize[0]), top + baseLine), (255, 255, 255), cv2.FILLED)
    cv2.putText(image, label, (left, top),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 1)


# Remove the bounding boxes with low confidence using non-maxima suppression
def postprocess(image, outp):
    # Initialize the parameters
    confidence_threshold = 0.7
    non_maximum_suppression_threshold = 0.4
    imageHeight = image.shape[0]
    imageWidth = image.shape[1]

    # Scan through all the bounding boxes output from the network and keep only the
    # ones with high confidence scores. Assign the box's class label as the class with the highest score.
    classIds = []
    confidences = []
    boxes = []
    for out in outp:
        for detection in out:
            scores = detection[5:]
            classId = np.argmax(scores)
            confidence = scores[classId]
            if confidence > confidence_threshold:
                center_x = int(detection[0] * imageWidth)
                center_y = int(detection[1] * imageHeight)
                width = int(detection[2] * imageWidth)
                height = int(detection[3] * imageHeight)
                left = int(center_x - width / 2)
                top = int(center_y - height / 2)
                classIds.append(classId)
                confidences.append(float(confidence))
                boxes.append([left, top, width, height])

    # Perform non maximum suppression to eliminate redundant overlapping boxes with
    # lower confidences.
    indices = cv2.dnn.NMSBoxes(
        boxes, confidences, confidence_threshold, non_maximum_suppression_threshold)
    for i in indices:
        i = i[0]
        box = boxes[i]
        left = box[0]
        top = box[1]
        width = box[2]
        height = box[3]
        drawPred(image, classIds[i], confidences[i], left,
                 top, left + width, top + height)


def load_model():
    global model
    model = cv2.dnn.readNetFromDarknet(
        "./YOLOv3/yolov3.cfg", "./YOLOv3/yolov3.weights")
    model.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    model.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)


def process(image):
    output_file_name = 'output.jpg'
    blob = cv2.dnn.blobFromImage(
        image, 1/255, (416, 416), [0, 0, 0], 1, crop=False)
    start_time = time.time()
    # Sets the input to the network
    model.setInput(blob)

    # Runs the forward pass to get output of the output layers

    outpout = model.forward(getOutputsNames(model))
    end_time = time.time()
    inference_time = end_time-start_time
    print("Inference time: ", inference_time)
    # Remove the bounding boxes with low confidence
    postprocess(image, outpout)

    # Write the image with the detection boxes
    cv2.imwrite(output_file_name, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    return inference_time


@app.route('/')
def index():
    return render_template('index.html')


@app.route("/predict", methods=["POST"])
def predict():
    if flask.request.json.get("image_encoded"):
        jpg_original = flask.request.json.get("image_encoded")
        prefix, encoded_string = jpg_original.split(',')
        image = Image.open(io.BytesIO(base64.b64decode(encoded_string)))
        image_np = np.array(image)
        inference_time = process(image_np)
        jpg_encoded = prefix + "," + base64.b64encode(
            cv2.imencode('.jpg', cv2.imread('output.jpg'))[1]).decode()
    return {"status": "success", "inference_time": inference_time, "image_encoded": jpg_encoded}


@app.route("/predict_file", methods=["POST"])
def predict_file():
    # ensure an image was properly uploaded to our endpoint
    if flask.request.method == "POST":
        if flask.request.files.get("image"):
            # read the image in PIL format
            image = flask.request.files["image"].read()
            image = Image.open(io.BytesIO(image))
            # preprocess the image and prepare it for classification
            image = np.array(image)
            process(image)
            image = cv2.imread('output.jpg')
            jpg_encoded = base64.b64encode(
                cv2.imencode('.jpg', image)[1]).decode()
    # return the data dictionary as a JSON response
    return {"status": "success", "image_encoded": jpg_encoded}


if __name__ == "__main__":
    load_model()
    app.run()
