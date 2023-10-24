from flask import Flask, render_template, request
# Additional imports from generate.py
import os
import json
from keras.models import load_model, Model  # Import the Model class
import pickle
import pandas as pd
import numpy as np
from keras.preprocessing.sequence import pad_sequences
from keras.preprocessing import image
from keras.applications.resnet50 import ResNet50, preprocess_input
from matplotlib import pyplot as plt




# Read the files word_to_idx.pkl and idx_to_word.pkl to get the mappings between word and index
word_to_index = {}
with open ("textData/word_to_idx.pkl", 'rb') as file:
    word_to_index = pd.read_pickle(file, compression=None)

index_to_word = {}
with open ("textData/idx_to_word.pkl", 'rb') as file:
    index_to_word = pd.read_pickle(file, compression=None)



print("Loading the model...")
model = load_model('model/model_1.h5')

resnet50_model = ResNet50 (weights = 'imagenet', input_shape = (224, 224, 3))
resnet50_model = Model (resnet50_model.input, resnet50_model.layers[-2].output)



# Generate Captions for a random image
# Using Greedy Search Algorithm

def predict_caption(photo):

    inp_text = "startseq"

    #max_len = 80 which is maximum length of caption
    for i in range(80):
        sequence = [word_to_index[w] for w in inp_text.split() if w in word_to_index]
        sequence = pad_sequences([sequence], maxlen=80, padding='post')

        ypred = model.predict([photo, sequence])
        ypred = ypred.argmax()
        word = index_to_word[ypred]

        inp_text += (' ' + word)

        if word == 'endseq':
            break

    final_caption = inp_text.split()[1:-1]
    final_caption = ' '.join(final_caption)
    return final_caption



def preprocess_image (img):
    img = image.load_img(img, target_size=(224, 224))
    img = image.img_to_array(img)

    # Convert 3D tensor to a 4D tendor
    img = np.expand_dims(img, axis=0)

    #Normalize image accoring to ResNet50 requirement
    img = preprocess_input(img)

    return img


# A wrapper function, which inputs an image and returns its encoding (feature vector)
def encode_image (img):
    img = preprocess_image(img)

    feature_vector = resnet50_model.predict(img)
    # feature_vector = feature_vector.reshape((-1,))
    return feature_vector


def runModel(img_name):
    #img_name = input("enter the image name to generate:\t")

    print("Encoding the image ...")
    photo = encode_image(img_name).reshape((1, 2048))



    print("Running model to generate the caption...")
    caption = predict_caption(photo)

    img_data = plt.imread(img_name)
    plt.imshow(img_data)
    plt.axis("off")

    #plt.show()
    print(caption)
    return caption

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    caption = ""
    if request.method == 'POST':
        # Check if 'image_file' was submitted in the form
        if 'image_file' in request.files:
            img_file = request.files['image_file']
            
            # Check if the file is not empty
            if img_file.filename != '':
                img_path = os.path.join("uploads", img_file.filename)
                img_file.save(img_path)
                
                # Generate caption
                caption = runModel(img_path)
                
                # Optionally, delete the uploaded image after processing
                os.remove(img_path)
            
    return render_template('index.html', caption=caption)


if __name__ == '__main__':
    app.run(debug=True)
