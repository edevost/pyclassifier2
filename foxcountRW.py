
import csv
import sys
import os
import cv2
import cv2.cv as cv
import numpy as np
import glob
from itertools import groupby
import time
from datetime import datetime,date
#from gi.repository import GExiv2
import shutil
import exiftool
import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.stats.stats import pearsonr
from scipy.stats.stats import linregress
import pylab
import random
import xlrd

# ***************************************************************************
# You first need to run generatemasks.py to generate the masks
# ***************************************************************************
imagesDir = "/home/edevost/Fox207/100801.F207.DB25/100RECNX/"
# Location of original images ################################################
#imagesDir = "/run/media/edevost/iomega1/Reconyx/RECONYX/Reconyx_2011/Fox145/110724.F145.DB33/100RECNX/"
#imagesDir = "/run/media/edevost/iomega1/Reconyx/RECONYX/Reconyx_2012/FOX145/20120626.F145.DB06/"
#imagesDir = "/run/media/edevost/iomega1/Reconyx/RECONYX/Reconyx_2012/FOX107/20120709.F107/"
#imagesDir = "/run/media/edevost/iomega1/Reconyx/RECONYX/Reconyx_2010/Fox207/100801.F207.DB25/100RECNX/"
#imagesDir = "/run/media/edevost/iomega1/Reconyx/RECONYX/Reconyx_2010/Fox134/100701.F134.Cam1/"

# Get images list -----------------
imglist = []
imglist = glob.glob(imagesDir + "/*.JPG")
print "done"

# get metadata -----------------------------------------
# Compiling regular expression search in metadata
date_reg_exp = re.compile(
                    '\d{4}[-/]\d{1,2}[-/]\d{1,2}\ \d{1,2}:\d{1,2}:\d{1,2}')
date_reg_expAM = re.compile(
                    '\d{4}[-/]\d{1,2}[-/]\d{1,2}\ \d{1,2}:\d{1,2}:\d{1,2}\ [AP][M]')
date_reg_exp2 = re.compile(
                    '\d{4}[:/]\d{1,2}[:/]\d{1,2}\ \d{1,2}:\d{1,2}:\d{1,2}')
listtags = []

with exiftool.ExifTool() as et:
    print "Loading metadata from images..."
    metadata = et.get_metadata_batch(imglist)
    #print "meta",metadata
    #check if EXIF key exist
    key = 'EXIF:DateTimeOriginal'
    #print "meta",metadata
    if key in metadata[0]:
        print "key found"
        tags1 = []
        for y in range(len(metadata)):
            tag = metadata[y]['EXIF:DateTimeOriginal']
            #print "tag", tag
            tags1.append(datetime.fromtimestamp(time.mktime(
                (time.strptime(tag,"%Y:%m:%d %H:%M:%S")))))
            #listtags.append(tag)
            #print listtags
        listtags.extend(tags1)
       # listtags.extend(tags1)
    else:
        print "key not found, looking in comments"
        tags1 = []
        for y in range(len(metadata)):
            key2 = 'File:Comment'
            if key2 in metadata[y]:
                tag2 = date_reg_expAM.findall(metadata[y]['File:Comment'])
                # account for AM PM, no AM PM if tag2 is empty
                if tag2 == []:
                    print "24h date format detected"
                    tag2 = date_reg_exp.findall(
                        metadata[y]['File:Comment'])
                    tag = ''.join(map(str, tag2))
                    tags1.append(datetime.fromtimestamp(time.mktime(
                    (time.strptime(tag,"%Y-%m-%d %H:%M:%S")))))
                else:
                    print "AM/PM date format detected"
                    tag = ''.join(map(str, tag2))
                    print "tag",tag
                #tag = metadata[y]['File:Comment'][0][0:35]
                # print "keys",metadata[y].keys()
                #print "metadata img 1",metadata[0]
                    tags1.append(datetime.fromtimestamp(time.mktime(
                        (time.strptime(tag,"%Y-%m-%d %I:%M:%S %p")))))
                #listtags.append(tag)
                #print listtags
            else:
                print "Problem with metadata, using FileModifyDate"
                tag2 = date_reg_exp2.findall(
                    metadata[y]['File:FileModifyDate'])
                tag = ''.join(map(str, tag2))
                tag = datetime.strptime(
                    tag,"%Y:%m:%d %H:%M:%S").strftime('%Y-%m-%d %H:%M:%S')
                tags1.append(datetime.fromtimestamp(time.mktime(
                    (time.strptime(tag,"%Y-%m-%d %H:%M:%S")))))
        listtags.extend(tags1)
print "DONE"

# sort imglist based on metadatas (listtags)
print "Sorting images from metadata"
imglist = [x for (y,x) in sorted(
    zip(listtags,imglist), key=lambda pair: pair[0])]
# sort listtags
listtags.sort()

# load generated masks
print "Loading masks and sorting masks"
resmasks = "/home/edevost/Renards/MasksResults/2010-F207-ori/04/temp4/"
#resmasks = "/run/media/edevost/Tycho/Renards/MasksResults/2010-F207-01/"
#resmasks = "/run/media/edevost/Tycho/Renards/MasksResults/2012-F145-01/"
#resmasks = "/run/media/edevost/Tycho/Renards/MasksResults/2012-F145-04/"
#resmasks = "/run/media/edevost/iomega1/MasksTests/2010-F207-01/04/temp4/"
#resmasks = "/run/media/edevost/iomega1/MasksTests/2010-F134-1701.F134.Cam1/temp10/"
#resmasks = "/run/media/edevost/iomega1/MasksTests/F2012-107/"
#resmasks = "/run/media/edevost/iomega1/MasksTests/2011-F145-01/110724.F145.DB33-100RECNX/"
#resmasks = "/run/media/edevost/iomega1/MasksTests/F2012-107-2/F2012-107/"
#resmasks = "/home/edevost/Renards2014/Phase2/NewFGest/foreground_detection_code/code/output/F2012-107/"
maskslist = glob.glob(resmasks + "/*.png")
maskslist.sort()
# remove first 4 images (background)
maskslist = maskslist[3:]

print maskslist[0]
print maskslist[-1]

######################################################################
# Foxes count ########################################################
# Actual script to count number of foxes in each images
# Functions Definitions
######################################################################
#----------------------------------------------------------------------
# Fucntion to display images if you run on test mode
def dispIm():
    if di == 1:
        cv2.namedWindow("Frame",cv2.WINDOW_NORMAL)
        cv2.namedWindow("Mask",cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Frame",900,601)
        #cv2.resizeWindow("Mask",600,301)
        cv2.moveWindow("Frame",10,30)
        cv2.moveWindow("Mask",20,20)
        cv2.imshow("Mask",Mask)
        cv2.imshow("Frame",Frame)
        k = cv2.waitKey(0) & 0xff
    elif di == 2:
        #cv2.namedWindow("ResIm",cv2.WINDOW_NORMAL)
        #cv2.setWindowProperty(
        #    "ResIm", cv2.WND_PROP_FULLSCREEN, cv2.cv.CV_WINDOW_FULLSCREEN)
        #cv2.moveWindow("ResIm",30,200)
        #cv2.imshow("ResIm",resim)
        cv2.imshow("Frame",Frame)
        k = cv2.waitKey(0) & 0xff    
        #cv2.destroyWindow("ResIm")
        #cv2.waitKey(0) & 0xff
    elif di == 3:
        cv2.namedWindow("Greyres",cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Greyres",900,601)
        cv2.moveWindow("Greyres",300,400)
        cv2.imshow("Greyres",greyres2) # greyres2
        k = cv2.waitKey(0) & 0xff
        cv2.imshow("Greyres",greyresE)
        k = cv2.waitKey(0) & 0xff
        cv2.destroyWindow("Greyres")
#----------------------------------

# Function to load original frame and original mask and find external contours
def loadF():
    currentFrame = cv2.imread(imglist[i]) #
    resizimg1 = cv2.resize(
            currentFrame,(0,0),fx=0.3,fy=0.3)# (0.3 works well)
    #workFrame  = resizimg1[80:-20,1:-10]
    workFrame  = resizimg1[100:-20,1:-10]
    #workFrame = cv2.copyMakeBorder(workFrame1,1,1,1,1,cv2.BORDER_CONSTANT,value=WHITE)
    workFramecp = workFrame.copy()
    workFrameGray = cv2.cvtColor(workFrame,cv2.COLOR_BGR2GRAY)
    # ---------------------------------------------------------
    currentMask1 = cv2.imread(maskslist[i])
    #currentMask2 = currentMask1[80:-20,1:-10]
    currentMask2 = currentMask1[100:-20,1:-10]
    # Slight opening to clean noise
    opened = cv2.morphologyEx(currentMask2, cv2.MORPH_OPEN, kernelO1)
    # find and draw external contours
    currentMaskOp1 = cv2.cvtColor(opened,cv2.COLOR_BGR2GRAY)
    # Perform small closing, to see
    currentMaskOp = cv2.morphologyEx(currentMaskOp1, cv2.MORPH_CLOSE, kernel)
    currentMask = cv2.convertScaleAbs(currentMaskOp)
    contoursE,hye = cv2.findContours(currentMask.copy(),
                                     cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    #print hye
    # cv2.CHAIN_APPROX_NONE
    return currentMask,contoursE,currentMask2,workFrame,workFramecp
#----------------------------------------------------------------------

# Function to load corresponding masks
def prepOb():
    #print "area test",cv2.contourArea(cnt)
    #dstmask1 = cv2.copyMakeBorder(currentMask2,1,1,1,1,cv2.BORDER_CONSTANT,value=255)
    dstmask = np.zeros(currentMask2.shape, dtype=np.uint8)
    #dstmask = np.zeros(dstmask1.shape, dtype=np.uint8)
    # needed for youngs seg
    h, w = dstmask.shape[:2]
    cv2.drawContours(dstmask,cnt,-1,(255,255,255),thickness=0) # -1
    cv2.fillPoly(dstmask,[cnt],WHITE)
    #print "cnt",cnt
    #mask = np.zeros((h+2, w+2), np.uint8)
    # floodfill mask
    #seed_pt = None
    #cv2.floodFill(dstmask, mask,seed_pt, (255, 255, 255), 1,1) # 5,5
    # invert image
    #dstmask = (255-dstmask)
    #dstmaskC = cv2.convertScaleAbs(dstmask)
    #dstmaskC = cv2.cvtColor(dstmask,cv2.COLOR_BGR2GRAY)
    resim = cv2.bitwise_and(workFrame,dstmask)
    dstmaskC = cv2.cvtColor(dstmask,cv2.COLOR_BGR2GRAY)
    return resim,dstmask,dstmaskC

# ----------------------------------------------------------------------

# Function to perform youg segmentation
def youngsSeg():
    # # if for contrast =================================
    # if sdGrey[0] > 0.7:
    #     #print "High contrast"
    #     clahe = cv2.createCLAHE(clipLimit=0.1, tileGridSize=(3,3))
    #     greyres2 = clahe.apply(greyres3)
    #     #greyres2 = greyres3
    #     kernel02 = np.ones((2,2),np.uint8) # erosion kernel
    # elif sdGrey[0] > 7:
    #     #print "Medium contrast"
    #     clahe = cv2.createCLAHE(clipLimit=0.1, tileGridSize=(3,3))# 16,16
    #     greyres2 = clahe.apply(greyres3)
    #     kernel02 = np.ones((2,2),np.uint8) # erosion kernel,
    # else:
    #     #print "Low contrast"
    #     clahe = cv2.createCLAHE(clipLimit=0.1, tileGridSize=(3,3))# 32,32
    #     greyres2 = clahe.apply(greyres3)
    #     kernel02 = np.ones((2,2),np.uint8) # erosion kernel,
    #clahe = cv2.createCLAHE(clipLimit=0.1, tileGridSize=(3,3))# 32,32
    #greyres2 = clahe.apply(greyres3)
    #kernel02 = np.ones((2,2),np.uint8) # erosion kernel,
    # end if for contrast =============================
    ##print "drawing contours on greyres2"
    if satI == 1:
        print "very bright image, mostly targetting bright regions in object"
        clahe = cv2.createCLAHE(clipLimit=16, tileGridSize=(32,32))# 32,32
        greyres2 = clahe.apply(greyres3)
        kernel02 = np.ones((2,2),np.uint8) # erosion kernel,
        cv2.drawContours(greyres2,cnt,-1,0,2) # 2 good
        greyres2 = cv2.copyMakeBorder(
            greyres2,5,5,5,5,cv2.BORDER_CONSTANT,value=0)
        th2,greyres = cv2.threshold(
            greyres2,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        goodhye = -1
    else:
        print "low saturation, targetting dark regions in object"
        clahe = cv2.createCLAHE(clipLimit=0.1, tileGridSize=(32,32))# 0.1,16,16
        greyres2 = clahe.apply(greyres3)
        kernel02 = np.ones((2,2),np.uint8) # erosion kernel (3,3)
        cv2.drawContours(greyres2,cnt,-1,255,2) # 2 good
        greyres2 = cv2.copyMakeBorder(
            greyres2,5,5,5,5,cv2.BORDER_CONSTANT,value=0)
        th2,greyres = cv2.threshold(
            greyres2,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
        goodhye = 1
    # apply adaptive threshold
    ##print "perform adaptive thresholding and small erosion"
    #greyres = greyres2
    # Border around image, for object touching border of image    
    #greyres = cv2.adaptiveThreshold(
    #         greyres2,255,cv2.ADAPTIVE_THRESH_MEAN_C,
    #             cv2.THRESH_BINARY_INV,11,1) # 11,2
    #greyres = cv2.threshold(150)
    # small erosion
    #greyresE = greyres
    greyresE = cv2.erode(greyres,kernel02,iterations = 1)
    # find contours INSIDE main blob and count
    contours2,hye2 = cv2.findContours(greyresE.copy(),
                    cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
    ##print hye2
    # --------------------------------
    # loop through hye2
    yincount = []
    aincount = []
    for io in range(len(hye2[0])):
        ##print "Iterating through inside objects"
        if hye2[0][io][3] == goodhye:
            ##print "Object inside main blob",io
            print "Inside contour area :",cv2.contourArea(contours2[io])
            # Object descriptors --------------------------------
            #dstmaskI = np.zeros(currentMask2.shape, dtype=np.uint8)
            dstmaskI = np.zeros(dstmask.shape, dtype=np.uint8)
            # needed for youngs seg
            hI, wI = dstmaskI.shape[:2]
            #cv2.drawContours(dstmaskI,contours2[i],2,(255,255,255),2) # -1 good
            cv2.drawContours(dstmaskI,contours2[io],-1,(255,255,255),-1) # -1 good
            ##print "cnt",cnt
            maskI = np.zeros((hI+2, wI+2), np.uint8)
            # floodfill mask
            seed_pt = None
            cv2.floodFill(dstmaskI, maskI,seed_pt, (255, 255, 255), 5, 5)
            # invert image
            dstmaskI = (255-dstmaskI)
            #dstmaskC = cv2.convertScaleAbs(dstmask)
            #dstmaskC = cv2.cvtColor(dstmask,cv2.COLOR_BGR2GRAY)
            resimI = cv2.bitwise_and(workFrame,dstmaskI)
            dstmaskCI = cv2.cvtColor(dstmaskI,cv2.COLOR_BGR2GRAY)
            greyres3I = cv2.cvtColor(resimI,cv2.COLOR_BGR2GRAY)
            hmaskI = cv2.calcHist([greyres3I],[0],dstmaskCI,[256],[0,256])
            meanGreyI = cv2.mean(greyres3I,dstmaskCI)
            relmeanGreyI = meanGreyI[0]/meanGreyIm[0]
            minmaxGreyI = cv2.minMaxLoc(hmaskI)
            #objHSV = cv2.cvtColor(resimI,cv2.COLOR_BGR2HSV)
            #meanHue = cv2.mean(objHSV,dstmaskCI)
            #HSVH = cv2.calcHist([objHSV],[0],dstmaskCI,[180],[0,180])
            #minmaxH = cv2.minMaxLoc(HSVH)
            #print "Mean grey value of inside object",meanGreyI[0]
            print "Mean relative grey of inside object",relmeanGreyI
            #print "Dominant grey value object INSIDE",minmaxGreyI[3][1]
            ##print "Mean Hue",meanHue[0]
            ##print "Dominant Hue",minmaxH[3][1]
            # end object descriptors -----------------------------------
            if cv2.contourArea(contours2[io]) < 20: # orig 5 (10)
                print "Inside object too small, discarting"
                ##print "--------"
                pass
            else:
                if satI ==1:
                    if relmeanGreyI > 0.05:
                        print "inside object bright enough"
                        yincount.append(1)
                    else:
                        print "inside object not bright enoug"
                        pass
                else:
                    if relmeanGreyI < 1.55:# and relmeanGreyI != 0:
                        print "inside object dark enough"
                        yincount.append(1)
                    else:
                        pass
                        print "inside object not dark enough"
            #elif relmeanGreyI > 1.5: ### orig > 1.5
            #    print "too bright, not likely a young"
                ##print "--------"
            #    pass
            #elif meanGreyI[0] < 1.0:
            #    print "grey mean = 0, not likely a young"
            #    ##print "--------"
            #    pass
            #else:
            #    yincount.append(1)
            #    #print "One young counted"
        else:
            print "Not a goodhye, passing to next object..."
            pass
    ycountIm.append(len(yincount))
    acountIm.append(sum(aincount))
    ##print "Numbers of youngs ",len(yincount)
    ##print "Numbers of adults ",len(aincount)
    ##print "-----------------------------------------------------"
    ##print hye2
    #cv2.imwrite("greyseg.png",greyresE)
    return greyres3,greyresE,greyres2,aincount,yincount,greyres

#----------------------------------------------------------------------
# Show images ?
sim = 1 # 0 = no, 1 = yes
# Configuration of opening and erosion
kernelO1 = np.ones((1,1),np.uint8) # First openening, clean noise (3,3) good
kernel = np.ones((10,10),np.uint8) # closing
#kernelerS = np.ones((3,3),np.uint8) # erosion kernel, segment youngs (maybe stronger with low meangrey)
#kernelO2 = np.ones((2,2),np.uint8) # Second opening, clean noise in youngsSeg (orig (2,2)
WHITE = (255,255,255)
# Initalise end variable count for one Den
ycount = []
acount = []
satsd = []
# Iterate though list of masks and count objects
si = 1000 #421 1750 521 4330 184 seq...1286 4157(SR),2301
starti = 4726 #4794 #185 820, 420, 1090, 1100
stopi = 4727
for i in range(maskslist.index(maskslist[starti]),maskslist.index(maskslist[stopi])):
#for i in range(len(maskslist)): # 739-750, great for diagnosis
#for i in range(len()): # 739-750, great for diagnosis
    ycountIm = []
    acountIm = []
    print "Analysing",maskslist[i]
    # Call function to load current Frame
    currentMask,contoursE,currentMask2,workFrame,workFramecp = loadF()    
    # Frames you want on display
    # *********************
    di = 1
    Frame = workFramecp
    Mask = currentMask
    if sim == 1:
        dispIm()
    else:
        pass
    # ******************************
    # calculate total areas to discard huge detected areas
    areas = [cv2.contourArea(c) for c in contoursE]
    Totareas = sum(areas)
    #print "-----------------------------------"
    #print "Total Area = ",Totareas
    #print "Total raw number of objects = ",len(contoursE)    
    #print "******* ******* ******* ******* ******* *******"    
    if Totareas < 1:
        #print "No object in image"
        ycount.append(0)
        acount.append(0)
    else:
        ############# Discard image if Totareas too large
        if Totareas > 40000: ###################################
            #print "Total area too large, discarting image"
            ycount.append(1000)
        else:
            #print "Good image, analysing content"
            #print "Iterating through external contours"
            blob = 1
            objlist = []
            for cnt in contoursE:
                #print "................."
                #print "Main object ",blob
                blob = blob +1
                extC = cv2.contourArea(cnt)
                print "Actual external contour area",extC
                # ------------
                #print "Loading coresponding mask..."
                resim,dstmask,dstmaskC = prepOb()
                # draw contour on main frame to see actual object
                cv2.drawContours(workFramecp,cnt,-1,255,2)
                grayforev = cv2.cvtColor(workFrame,cv2.COLOR_BGR2GRAY)
                meanGreyIm = cv2.mean(grayforev)
                workFrameHSV = cv2.cvtColor(workFrame, cv2.COLOR_BGR2HSV)
                strangeMeanGrey,sdGreyI = cv2.meanStdDev(grayforev)
                meanHUE = cv2.mean(workFrameHSV)
                #print "strange mean, sd",strangeMeanGrey,sdGrey
                #if meanHUE[1] > 40 and sdGreyI[0] > 40: # 120 (100 et 50) for 2010 207
                if meanHUE[2] > 130:
                    satI = 1
                else:
                    satI = 0
                if sdGreyI[0] > 40:
                    sdG = 1
                else:
                    sdG = 0
                print "mean HUE of workframe",meanHUE
                #print "mean luminosity of grey image :",meanGreyIm[0]
                print "sd of grey image: ",sdGreyI
                greyres3 = cv2.cvtColor(resim,cv2.COLOR_BGR2GRAY)
                greyres3R = (greyres3/meanGreyIm[0]).astype(np.float32)
                # ------------------------------------------------
                # grey descriptors
                hist_Greymask = cv2.calcHist([greyres3],
                                             [0],dstmaskC,[256],[0,256])
                hist_GreymaskR = cv2.calcHist([greyres3R],
                                              [0],dstmaskC,[256],[0,2])
                #print hist_GreymaskR
                # Relative histogram==============================
                perB = sum(hist_GreymaskR[200:])/float(extC)
                perL = sum(hist_GreymaskR[:30])/float(extC) # 30
                #print "Percentage of relative bright pixels in mask",perB
                #print "Percentage of relative dark pixels in mask",perL
                meanGrey = cv2.mean(greyres3,dstmaskC)
                strangeMeanGrey,sdGrey = cv2.meanStdDev(greyres3R,dstmaskC)
                minmaxGrey = cv2.minMaxLoc(hist_Greymask)
                relGreyWO = meanGrey[0]/meanGreyIm[0]
                # store grey descriptors values
                descriptors = list([perB[0],perL[0],sdGrey[0][0],extC])
                print "Object descriptors (perB,perL,sdGrey,extC)",descriptors
                print "meanGrey,relMeanGrey",meanGrey,relGreyWO
                # Display image
                # ************
                di = 2
                if sim ==1:
                    dispIm()
                else:
                    pass
                #     # ----------------------------------------
                if satI == 1:
                    print "high saturation, targetting bright regions"
                    if extC > 200:# (original 150)                   
                        # call for young segmentation
                        if sdGrey > 0.30: #(orig 0.17, 30 for good est)
                            print "sdGrey of object large, probable adult"
                            acountIm.append(1)
                        else:
                            print "probable group of young, segmenting"
                            #print "Object large enough, segmenting"
                            (greyres3,greyresE,greyres2
                             ,yincount,aincount,greyres) = youngsSeg()
                            #ycountIm.append(1)
                            #**************
                            di = 3
                            if sim == 1:
                                dispIm()
                            else:
                                pass
                            # ************************************
                    elif extC > 50: # orig 50
                        if relGreyWO < 0.95:
                            print "object not bright enough, not counting"
                            pass
                        else:
                            print "probable young alone"
                            ycountIm.append(1)
                    else:
                        pass
                    # ----------------------------------------
                if satI == 0:
                    print "low saturation, targetting dark regions"
                    if extC > 200:# (original 100) 600 for al lot with 0.001                   
                        # call for young segmentation
                        if sdGrey > 0.20: #(orig 0.17) 30
                            print "sdGrey to large, probable adult"
                            acountIm.append(1)
                        else:
                            print "probable group of young, segmenting"
                            #print "Object large enough, segmenting"
                            (greyres3,greyresE,greyres2
                             ,yincount,aincount,greyres) = youngsSeg()
                            #ycountIm.append(1)
                            di = 3
                            if sim == 1:
                                dispIm()
                            else:
                                pass
                    elif extC > 50: # orig 50, 300, 150 very good
                        if relGreyWO > 0.95:
                            print "object not dark enough, not counting"
                            pass
                        else:
                            print "probable young alone"
                            ycountIm.append(1)
                    else:
                        print "object too small, passing"
                        pass
                    # ----------------------------------------                  
                #obtype = raw_input("objtype :")
                #descriptors.append(obtype)
                #myfileD = open('descriptorsTMP.csv', 'a')
                #wr = csv.writer(myfileD)
                #wr.writerow(descriptors)
                #myfileD.close()
            #print "Number of young IN each objects :",ycountIm
            #print "Total number of youngs in image :",sum(ycountIm)
            #print "Total number of adults in image :",acountIm
            ycount.append(sum(ycountIm))
            acount.append(sum(acountIm))
            #print ycount
            #cv2.imwrite("orig.png",workFrame)
            if sim == 1:
                cv2.destroyAllWindows()
                cv2.waitKey(0) & 0xff
                cv2.waitKey(0) & 0xff
                cv2.waitKey(0) & 0xff
                cv2.waitKey(0) & 0xff
                cv2.waitKey(0) & 0xff
                cv2.waitKey(0) & 0xff
                cv2.waitKey(0) & 0xff
                cv2.waitKey(0) & 0xff
                cv2.waitKey(0) & 0xff
                cv2.waitKey(0) & 0xff
            else:
                pass
    print ycount

    
    if meanHUE[2] > 130:
        satsd.append(1)
    else:
        satsd.append(0)
myfile = open('../SoftCounts/2010-F207-J-ori-32-closing(10)-small(50).csv', 'w')
wr = csv.writer(myfile)
wr.writerow(ycount)
myfile.close()
myfile2 = open('../SoftCounts/2010-F207-A-ori-32-closing(10)-small(50).csv', 'w')
wr = csv.writer(myfile2)
wr.writerow(acount)
myfile2.close()
##print "DONE"

####################################################################
####################################################################
# correll with camille count
# load camille data, one file -----------------------------
frame = pd.DataFrame()
#xl = pd.ExcelFile("/home/edevost/Renards2014/Phase2/DataCamilleComplete/watchs/2011/tab_2011_FOX145.xlsx")
xl = pd.ExcelFile("/home/edevost/Renards/DataCamilleComplete/watchs/2010/tab_2010_Fox207.xlsx")
#xl = pd.ExcelFile("/run/media/edevost/Tycho/Renards/DataCamilleComplete/watchs/2010/tab_2010_Fox207.xlsx")
#xl = pd.ExcelFile("/home/edevost/Renards2014/Phase2/DataCamilleComplete/watchs/2010/tab_2010_Fox207.xlsx")

#xl = pd.ExcelFile("/run/media/edevost/Tycho/Renards/DataCamilleComplete/watchs/2012/tab_2012_FOX145.xlsx")

#xl = pd.ExcelFile("/home/edevost/Renards2014/Phase2/DataCamilleComplete/watchs/2010/tab_2012_Fox134.xlsx")
#xl = pd.ExcelFile("/home/edevost/Renards2014/Phase2/DataCamilleComplete/watchs/2012/tab_2012_FOX107.xlsx")

dfCt = xl.parse(0)
dfC = dfCt.ix[:,['Photo','Annee','Taniere','AM','ANM','J']] # F134 JNM
print "DONE"


# select good section

# for 2012 F145
#dfCS = dfC[1631:1631 + 3900]
#print dfCS

# for 2011 fox 145
#dfCS = dfC[2720:2720 + 600]
#print dfCS
# for 2012 fox 107 ############
#dfCS = dfC[207:207+1689]
#dfCS = dfC[207:207+200]
# ---------------------------

#for 2010-Fox207 100801.F207.DB25/100RECNX/
#dfCS = dfC[715:715+746]
#dfCS = dfC[715:715+5063]
dfCS = dfC[715:715+4900] # 4900
print dfCS
#dfCS = dfC[715:715+5050]
# ---------------------------

# for 2010 fox 134-100701-cam1 (JNM)
#dfCS = dfC[0:2475]
#dfCS = dfC[0:2300]
#dfCS = dfC[0:100]
#print dfCS

# Add a TotAn (Total animaux) in 8th columns of dataframe
columns2 = ['AM','ANM','J']
dfCS['TotAn'] = dfCS[columns2].sum(axis=1)
print "done"
# add presence absence data
dfCS['PresAbs'] = (dfCS['TotAn']>0).astype(int)
print dfCS

# Add a TotAn (Total animaux) in 8th columns of dataframe
#columns2 = ['AM','ANM','JNM']
#dfCS['TotAn'] = dfCS[columns2].sum(axis=1)
#print "done"
# add presence absence data
#dfCS['PresAbs'] = (dfCS['TotAn']>0).astype(int)
# create results dataframe
#camC = dfC['TotAn'] we have to load dfC (see beginning of file)
#dfC1 = dfCS[0:2475]
#camC = list(dfC1['JNM'])
#camC = camC1[0:5059]
#camC = [0:5063]
# add count datas in dataframe
#dfCS['SoftC'] = objcount[0:5049]
# read ycount from file

my_data = np.genfromtxt('../SoftCounts/2010-F207-J-ori-32-closing(10)-small(50).csv', delimiter=',')
ycountT = map(int,my_data)
#ycountT = ycount
dfCS['SoftC'] = ycountT
print dfCS
# add presence absence for visual count
presab = []
# create a presence absence vector fo objcount
for item in ycountT:
#for item in objcount:    
    if item != 0:
        presab.append(1)
    else:
        presab.append(0)
print "DONE"
# add to dataframe
dfCS['SoftPresAbs'] = presab
# Remove camera fall

#dfCS = dfCS[:4970]
# add saturation values (0,1)
dfCS['sat'] = satsd[0:4900]
# Remove 1000 values
dfCS1 = dfCS[dfCS['SoftC']==1000]
dfCS2 = dfCS[dfCS['SoftC']!=1000]
# remove high count
# remove firsts five images
dfCS3A = dfCS2

dfCS3 = dfCS3A[dfCS3A['SoftC'] < 25]

#dfCS3 = dfCS2
# Remove Visual count 0 class
#dfCS2 = dfCS[dfCS['JNM']!=0]
#dfCS2 = dfCS1

# -----------------------------------------------
#### see zero counts Camille with large count software
dfCS0 = dfCS[dfCS['JNM']==0]
#### Query 0 count for me and count for C
dfCSM0 = dfCS2[dfCS2['SoftC']==0]
# --------------------------------------------------

# Create lists for corellation
camC1 = list(dfCS3['J'])
objc = list(dfCS3['SoftC'])
               
slopeO, interceptO, r_valueO, p_valueO, std_errO = linregress(camC1,objc)
print "r squared count = ",r_valueO**2
r_valueO = r_valueO**2
print "slope",slopeO
print "p-value",p_valueO


# plot raw corellation
plt.scatter(camC1,objc)
#plt.title('Obj count: erode = %s, dilate = %s, thres = %s'%(er,dil,thres))
plt.xlabel('Visual count')
plt.ylabel('Software count')
#pylab.savefig(resultsdir + 'ObjCount-' + str(count) + '.pdf',bbox_inches='tight')
plt.show()

# plot mean with sd
dfgrouped = dfCS3.groupby(['J','SoftC'],as_index=True)
#table1 = dfCS3.pivot_table(rows='JNM',aggfunc={"SoftC":[np.mean,np.std]})
table1 = dfCS3.pivot_table(index='J',aggfunc={"SoftC":[np.mean,np.std]})

plt.errorbar(table1['SoftC'].index,table1['SoftC']['mean'],
             table1['SoftC']['std'],fmt='-o',color="black")
plt.xlabel('Visual count')
plt.ylabel('Software count')
plt.text(-0.5,5.5,'N = %s frames\n  $R^2$= %s\n' r' $\beta$ = %s'%(len(dfCS3),round(r_valueO,2),round(slopeO,2)))
plt.xlim(-1,18)
plt.gray()
plt.show(
)

# number of images to show with RS
imgRS = dfCS3[dfCS3['SoftC'] > 3 ]

print len(dfCS3[dfCS3['SoftC'] >= 16 ])
print dfCS3[dfCS3['SoftC'] >= 16 ]

# see where mismatches occurs
dfCS3['MissM'] = dfCS3['SoftC']-dfCS3['J']

# select highest missmatch
print dfCS3[dfCS3['MissM']>=5] # 229 overestimated missmatch)
print len(dfCS3[dfCS3['MissM']>=5]) # 229 overestimated missmatch)
 
print dfCS3[dfCS3['MissM']<=-5] # 488 underestimated missmatch)

dfCS3MML = dfCS3[dfCS3['MissM']<=-5]
print dfCS3MML[dfCS3MML['sat']==0]


print len(dfCS3[dfCS3['MissM']<=-5]) # 488 underestimated missmatch)

# select highest missmatch
print dfCS3[dfCS3['MissM']>=10] # 40 highly overestimated missmatch

print dfCS3[dfCS3['MissM']<=-10] # 7 highly underestimated missmatch



# select Camcount 0
print dfCSred[dfCSred['TotAn']==0]

# select softcount 0
# select Camcount 0
print dfCSred[dfCSred['SoftC']==0]

tmp1 = dfCSred[dfCSred['SoftC']==1]
print tmp1

print tmp1[tmp1['MissM']<-3]
###################################################






