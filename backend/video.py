###
### module for video processing
###

import time
from imutils.perspective import four_point_transform
from imutils import contours
import imutils
import cv2
import numpy as np

# define the dictionary of digit segments so we can identify
# each digit.
DIGITS_LOOKUP = {
	(1, 1, 1, 0, 1, 1, 1): 0,
	(0, 0, 1, 0, 0, 1, 0): 1,
	(1, 0, 1, 1, 1, 1, 0): 2,
	(1, 0, 1, 1, 0, 1, 1): 3,
	(0, 1, 1, 1, 0, 1, 0): 4,
	(1, 1, 0, 1, 0, 1, 1): 5,
	(1, 1, 0, 1, 1, 1, 1): 6,
	(1, 0, 1, 0, 0, 1, 0): 7,
	(1, 1, 1, 1, 1, 1, 1): 8,
    (1, 1, 1, 1, 0, 1, 1): 9
}

FP_MARGIN = 5


# For debugging.
def showimg(img):
    cv2.imshow('img', img)
    cv2.waitKey(0)


# Read data from camara in Raspberry Pi, extract remaining
# time data by seven segment recognition. Return remaining
# time is success, -1 otherwise.
def get_remaining_time():
    try:
        # Open, Read an image.
        # TODO: Change this to video from Raspberry Pi.
        image = cv2.imread("example2.png")
        image = imutils.resize(image, height=500)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 50, 200, 255)

        cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        digitCnts = []
        for c in cnts:
            (x, y, w, h) = cv2.boundingRect(c)
            if (w >= 15):
                digitCnts.append(c)

        # Create rectangle containing LCD, for four point transformation.
        rect = [list(map(int, cv2.boxPoints(cv2.minAreaRect(cnts[3]))[0])),
                list(map(int, cv2.boxPoints(cv2.minAreaRect(cnts[3]))[1])),
                list(map(int, cv2.boxPoints(cv2.minAreaRect(cnts[0]))[2])),
                list(map(int, cv2.boxPoints(cv2.minAreaRect(cnts[0]))[3]))]
        rect[0][0] -= FP_MARGIN
        rect[0][1] += FP_MARGIN
        rect[1][0] -= FP_MARGIN
        rect[1][1] -= FP_MARGIN
        rect[2][0] += FP_MARGIN
        rect[2][1] -= FP_MARGIN
        rect[3][0] += FP_MARGIN
        rect[3][1] += FP_MARGIN

        # Perform four point transform with rectangle created above.
        image = four_point_transform(image, np.array(rect, dtype=int))
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 50, 200, 255)

        cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        digitCnts = []
        for c in cnts:
            (x, y, w, h) = cv2.boundingRect(c)
            if (w >= 15):
                digitCnts.append(c)

        digitCnts = contours.sort_contours(digitCnts, method='left-to-right')[0]
        digits = []
        thresh = cv2.threshold(gray, 0, 255,
                               cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (1, 5))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        for c in digitCnts:
            (x, y, w, h) = cv2.boundingRect(c)
            # if width is small enough, we recognize it as `1`.
            if (w < 45):
                digits.append(1)
                continue
            roi = thresh[y:y+h, x:x+w]
            # compute the width and height of each of the 7 segments
            # we are going to examine
            (roiH, roiW) = roi.shape
            (dW, dH) = (int(roiW * 0.25), int(roiH * 0.15))
            dHC = int(roiH * 0.05)
            # define the set of 7 segments
            segments = [
                ((0, 0), (w, dH)),  # top
                ((0, 0), (dW, h // 2)),  # top-left
                ((w - dW, 0), (w, h // 2)),  # top-right
                ((0, (h // 2) - dHC), (w, (h // 2) + dHC)),  # center
                ((0, h // 2), (dW, h)),  # bottom-left
                ((w - dW, h // 2), (w, h)),  # bottom-right
                ((0, h - dH), (w, h))  # bottom
            ]
            on = [1] * len(segments)
            # loop over the segments
            for (i, ((xA, yA), (xB, yB))) in enumerate(segments):
                # extract the segment ROI, count the total number of
                # thresholded pixels in the segment, and then compute
                # the area of the segment
                segROI = roi[yA:yB, xA:xB]
                total = cv2.countNonZero(segROI)
                area = (xB - xA) * (yB - yA)
                # if the total number of non-zero pixels is greater than
                # 50% of the area, mark the segment as "on"
                if total / float(area) > 0.5:
                    on[i] = 0
            # lookup the digit and draw it on the image
            digit = DIGITS_LOOKUP[tuple(on)]
            digits.append(digit)
        return digits[0] * 1000 + digits[1] * 100 + digits[2] * 10 + digits[3]
    except Exception:
        return -1


if __name__ == '__main__':
    for i in range(10):
        print(get_remaining_time())
        time.sleep(5)