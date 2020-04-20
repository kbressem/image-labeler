# Image Labeler
A simple prototype for image labeling, supporting PNG, JPEG, BMP, GIF and DICOM.  
Adapted from a script provided by [acbetter](https://gist.github.com/acbetter/32c575803ec361c3e82064e60db4e3e0) (https://acbetter.com/)

## Prerequisites
The script was written under `Python 3.7`using `PyQt5`. 
For DICOM support `PyDicom`, `numpy` and `PIL` were used. (https://pydicom.github.io/pydicom/stable/tutorials/installation.html)
For export of labels to csv `pandas` is used.

The following versions of python libraries were included
```
    PyQt5
    Python 3.7.4
    PyDicom 1.4.2
    numpy 1.17.2
    PIL 6.2.0
    pandas 0.25.1
```


## How to use
Adapt the `labels.txt` file to implement custom labels. Each category should be in a single line. Different classes should be separated by a colon. An unlimited number of categories and classes is supported.

After start press `Ctrl+O` (or `Cmd+O` on Mac) to open an image directory. Depending on the number of images and the number of subdirectories, loading can take some time and the programm might appear unresponsive. 

The previous or next image can be selected with the arrow keys. Each time the arrow keys are pressed, labels will be written to a file (`ORIGINALNAME_annotation.txt`) in the same directory as the image file. 

Further commands can be found in the menu strip under `View`.
  
Sample images taken from:   
https://commons.wikimedia.org/wiki/File:Chest.png  
https://en.wikipedia.org/wiki/Pneumothorax#/media/File:Rt_sided_pneumoD.jpg  
https://en.wikipedia.org/wiki/Projectional_radiography  
