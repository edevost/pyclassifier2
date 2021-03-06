
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
from numpy import genfromtxt
#import matplotlib.dates as dates

# load images to test
#imagesDir = "/run/media/edevost/iomega1/Reconyx/RECONYX/Reconyx_2012/FOX145/20120626.F145.DB06/"
#imagesDir = "/run/media/edevost/iomega1/Reconyx/RECONYX/Reconyx_2011/Fox145/110724.F145.DB33/100RECNX/"
imagesDir = "/run/media/edevost/iomega1/Reconyx/RECONYX/Reconyx_2010/Fox207/100801.F207.DB25/100RECNX/"
#imagesDir = "/run/media/edevost/iomega1/Reconyx/RECONYX/Reconyx_2010/Fox134/100701.F134.Cam1/"
#imagesDir = "/run/media/edevost/iomega1/Reconyx/RECONYX/Reconyx_2012/FOX107/20120709.F107/"

# create temporary directory in imagesDir
if not os.path.exists(imagesDir + "temp1"):
    os.makedirs(imagesDir + "temp1")
temp1 = os.path.join(imagesDir,"temp1/")

#remtemp1 = temp1 + "*.jpg" #*** might be needed.

#remtemp1 = "/run/media/edevost/iomega1/Reconyx/RECONYX/Reconyx_2010/Fox207/100801.F207.DB25/100RECNX/temp1/*.jpg"


# Need to specify here the location of the compiled c++ libraries.
######################################################################
# cpp executable.
cppex = './cpplibs/background_estimation_code/code/EstimateBackground'
cppex2 = './cpplibs/foreground_detection_code/code/ForegroundSegmentation'
# c++ executable
cppcom1 = [cppex,temp1,"EstBG"]
cppcom = " ".join(cppcom1)
# 
cppcom2 = [cppex2,temp1,"2010-F207-01"]
paramsdir = "./cpplibs/foreground_detection_code/code/"
cppfg = " ".join(cppcom2)
######################################################################
# in cpplibs/foreground_detection_code/code/main.cpp
# you need to specify output path and params.txt path
######################################################################
# End cpp libraries section

# Get images list -----------------
imglist = []
imglist = glob.glob(imagesDir + "/*.JPG") # fix this...
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
imglist = [x for (y,x) in sorted(
    zip(listtags,imglist), key=lambda pair: pair[0])]

# sort listtags
listtags.sort()

# get IMPG
# compute time diffs from first image

maxgap = 5
impg = []
res = []
for x in listtags:
    diff = int((x - listtags[0]).total_seconds())
    res.append(diff)
groups = [[res[0]]]
for y in res[1:]:
    if abs(y - groups[-1][-1]) <= maxgap:
        groups[-1].append(y)
    else:
        groups.append([y])
    # get values impg and nseq
impgtemp = []
for group in groups:
    impgtemp.append(len(group))
impg.extend(impgtemp)
print "done"
# Select images we want
# Get high img count
# get index of wanted sequence
#print impg.index(285)
#idx = impg.index(285)

# function to compute best maxgap

tempimpg2 = impg
for y in range(3):
    tempimpg = []
    for x in range(len(tempimpg2)): # range 3, adjust if needed
        #print impg[x]
        if tempimpg2[x] <= 30:
            tempimpg.append(tempimpg2[x])
        elif 30 < tempimpg2[x] < 100:
            #print impg[x]
            tempimpg.append(tempimpg2[x]-30)
            tempimpg.append(tempimpg2[x]-(tempimpg2[x]-30))
        elif 100 <= tempimpg2[x] <= 200:
            #print impg[x]
            tempimpg.append(tempimpg2[x]-75)
            tempimpg.append(tempimpg2[x]-(tempimpg2[x]-75))
        else:
            tempimpg.append(tempimpg2[x]-100)
            tempimpg.append(tempimpg2[x]-(tempimpg2[x]-100))
    tempimpg2 = tempimpg


impg = tempimpg    
print impg        


# Background estimation and foreground segmentation
#for sequence in range(5):
#sequence = 1 # 289
for sequence in range(len(impg)):
    print "Analysing sequence ",sequence+1 ### xx
    # resize images
    for image in range(impg[sequence]):
        #print "image",image
        currentFrame = cv2.imread(imglist[image + int(sum(impg[0:sequence]))])
        print "img",imglist[image + int(sum(impg[0:sequence]))]
        # convert to grayscale
        imggray1 = cv2.cvtColor(currentFrame.copy(),cv2.COLOR_BGR2GRAY)
        # crop gray img
        imggray2 = imggray1[120:-10,1:-10]
        print "img avg brightness",cv2.mean(imggray2)
        avgB = cv2.mean(imggray2)
        outf = open(os.path.join(paramsdir, 'params.txt'),'w')
        if avgB[0] < 100.0:
            print "low light, using 0.01",avgB
            outf.write(str(0.01))
        else:
            print "enough light, using 0.0011",avgB
            outf.write(str(0.01)) # 0.0011
        #print "Resizing",image+1
        #r = 651.0 / currentFrame.shape[1]
        #dim = (651, int(currentFrame.shape[0] * r ))
        resizimg1 = cv2.resize(
            currentFrame,(0,0),fx=0.3,fy=0.3)# (0.3 works well)
        #resizimg1 = cv2.resize(currentFrame, dim, interpolation = cv2.INTER_AREA)
        # crop top and bottom image
        #resizimg = resizimg1
        # save resized frame to temp dir
        cv2.imwrite(os.path.join(temp1,
            os.path.basename(imglist[image + int(sum(
                impg[0:sequence]))])[0:-4]+".jpg"), resizimg1)
    # call c++ executable to estimate background
    os.system(cppcom)
    # call c++ executable to subtract background
    os.system(cppfg)    
    # clean tmpdir
    #
    for the_file in os.listdir(temp1):
        file_path = os.path.join(temp1, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception, e:
            print e



######################################################################
######################################################################
######################################################################

# # load results and perform count
# resmasks = "/home/edevost/Renards2014/Phase2/NewFGest/foreground_detection_code/code/output/F2012-107/"
# #resmasks = "/run/media/edevost/iomega1/MasksTests/2010-F207-01/04/temp4/"
# #resmasks = "/run/media/edevost/iomega1/MasksTests/2010-F134-1701.F134.Cam1/temp10/"

# maskslist = glob.glob(resmasks + "/*.png")
# maskslist.sort()
# # remove first 3
# maskslist = maskslist[3:]

# print maskslist[0]
# print maskslist[-1]


  
# # Analyse images ###############################################
# #################################################################
# # select 100 random images
# randvect = random.sample(range(1, 5063), 100)

# print randvect

# kernelerY = np.ones((3,3),np.uint8) # opening kernel
# kernelerZ = np.ones((10,10),np.int8) # closing kernel 
# kerneler = np.ones((5,5),np.uint8) # erosion kernel
# # count monsters
# objcount = []
# areacount = []
# si = 4300 # 729 (light) good for test young seg and 82 and 4300 (low light)
# # 823 impressionnant
# npts = []
# for i in range(len(maskslist[si:si+1])): # 739-750, great for diagnosis
#     print "Analysing",maskslist[si]
#     currentFrame = cv2.imread(imglist[si]) # load corresponding frame
#     resizimg1 = cv2.resize(
#             currentFrame,(0,0),fx=0.3,fy=0.3)# (0.3 works well)
#     workFrame  = resizimg1[80:-20,1:-10]    
#     workFrameHSV = cv2.cvtColor(workFrame, cv2.COLOR_BGR2HSV)
#     workFrameLAB = cv2.cvtColor(workFrame, cv2.COLOR_BGR2LAB)
#     B,G,R = cv2.split(workFrame)
#     Bp = (B - np.mean(B))/np.std(B)
#     Gp = (G - np.mean(G))/np.std(G)
#     Rp = (R - np.mean(R))/np.std(R)
#     # ---------------------------------------------------------
#     currentMask1 = cv2.imread(maskslist[si])
#     currentMask2 = currentMask1[80:-20,1:-10]
#     # Opening
#     opened = cv2.morphologyEx(currentMask2, cv2.MORPH_OPEN, kernelerY)
#     #opened = currentMask2
#     # closing
#     #closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernelerZ)
#     # find and draw contours
#     currentMaskOp = cv2.cvtColor(opened,cv2.COLOR_BGR2GRAY)
#     currentMask = cv2.convertScaleAbs(currentMaskOp)
#     #contours,_ = cv2.findContours(currentMask,
#     #                              cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
#     contours,hye = cv2.findContours(currentMask.copy(),
#                                     cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
#     areas = [cv2.contourArea(c) for c in contours]
#     print "Number of monsters",len(contours)
#     print "Total Area",sum(areas)    
#     # ----------------------------------------------
#     # for evey contours,analyse corresponding blob
#     white = (255, 255, 255)
#     #dstmask = np.zeros(currentMask2.shape, dtype=np.uint8)    
#     for cnt in contours:
#         objV = []
#         workFramecp = workFrame.copy()
#         print "Area",cv2.contourArea(cnt)
#         area = cv2.contourArea(cnt)
#         dstmask = np.zeros(currentMask2.shape, dtype=np.uint8)
#         h, w = dstmask.shape[:2]        
#         cv2.drawContours(dstmask,cnt,-1,(255,255,255),-1)
#         mask = np.zeros((h+2, w+2), np.uint8)
#         # floodfill mask
#         seed_pt=None
#         cv2.floodFill(dstmask, mask,seed_pt, (255, 255, 255), 5, 5)
#         # invert image
#         dstmask = (255-dstmask)
#         #dstmaskC = cv2.convertScaleAbs(dstmask)
#         dstmaskC = cv2.cvtColor(dstmask,cv2.COLOR_BGR2GRAY)
#         resim = cv2.bitwise_and(workFrame,dstmask)
#         # display contours on original image
#         out = opened.copy()
#         cv2.drawContours(out,cnt,-1,255,2)
#         # Colors descriptors ----------------------------------------
#         # hist_mask = cv2.calcHist([workFrame],[0],dstmaskC,[256],[0,256])
#         hsv_hist = cv2.calcHist([workFrameHSV],
#                     [0,1,2],dstmaskC,[180,256,256],[0,180,0,256,0,256])
#         hsvH = cv2.calcHist([workFrameHSV], [0], dstmaskC, [180], [0, 180])
#         hsvS = cv2.calcHist([workFrameHSV], [1], dstmaskC, [255], [0, 255])
#         StB_hist = cv2.calcHist(
#             [Bp.astype('float32')],[0], dstmaskC, [100], [-10,10])
#         StG_hist = cv2.calcHist(
#             [Gp.astype('float32')],[0], dstmaskC, [100], [-10,10])
#         StR_hist = cv2.calcHist(
#             [Rp.astype('float32')],[0], dstmaskC, [100], [-10,10])
#         # hsvV = cv2.calcHist([workFrameHSV], [2], dstmaskC, [255], [0, 255])
#         # labH = cv2.calcHist([workFrameLAB], [0], dstmaskC, [100], [0, 100])
#         # # store values
#         meanB = cv2.mean(Bp,dstmaskC)
#         meanG = cv2.mean(Gp,dstmaskC)
#         meanR = cv2.mean(Rp,dstmaskC)
#         minmaxB = cv2.minMaxLoc(StB_hist)
#         minmaxG = cv2.minMaxLoc(StG_hist)
#         minmaxR = cv2.minMaxLoc(StR_hist)
#         # print results
#         print "mean B G R :",meanB[0],meanG[0],meanR[0]
#         print "dominant B G R :",minmaxB[3][1],minmaxG[3][1],minmaxR[3][1]
#         meanHSV = cv2.mean(workFrameHSV,dstmaskC)
#         meanS = cv2.mean(workFrameHSV,dstmaskC)
#         minmaxS = cv2.minMaxLoc(hsvS)
#         # minmaxV = cv2.minMaxLoc(hsvV)
#         minmaxH = cv2.minMaxLoc(hsvH)
#         # minmaxL = cv2.minMaxLoc(labH)
#         # --- print results
#         # is it bright
#         # print "Mean brightness", meanHSV[2]
#         # print "Dominant brightness", minmaxV[3][1]
#         # # if bright, is the color good for fox ?
#         print "Dominant Color", minmaxH[3][1]
#         print "Mean Color", meanHSV[0]
#         print "Dominant Sat",minmaxS[3][1]
#         print "Mean Sat",meanHSV[1]
#         # # is th saturation good for fox ?
#         # print "Mean Saturation" ,meanHSV[1]
#         # print "Dominant Saturation",minmaxS[3][1]
#         # Youngs segmentation ****************************************
#         # ------------------------------------------------------------
#         ksegO = np.ones((5,5),np.uint8) # opening kernel
#         ksegE = np.ones((1,1),np.uint8) # erode kernel        
#         # Convert to gray
#         greyres3 = cv2.cvtColor(resim,cv2.COLOR_BGR2GRAY)
#         # grey descriptors
#         hist_mask = cv2.calcHist([greyres3],[0],dstmaskC,[256],[0,256])
#         # hsv_hist = cv2.calcHist([greyres],[0,1,2],dstmaskC,[180,256,256],[0,180,0,256,0,256])
#         #weighted = H/S
#         #H,S,V = cv2.split(workFrameHSV)
#         # weightH = workFrameHSV[:,:,0].astype(np.float)/workFrameHSV[:,:,1].astype(np.float)
#         # weightHistH = cv2.calcHist([workFrameHSV], [0], dstmaskC, [50], [0,180])
#         # weightHistS = cv2.calcHist([workFrameHSV], [1], dstmaskC, [50], [0,180])
#         # weightedH = cv.CalcProbDensity(weightHistS, weightHS, dst_hist, scale=255)        
#         #meanWH = cv2.mean(weightH,dstmaskC)
#         #print "npmin",np.min(workFrameHSV[:,:,1])
#         #print weightH
#         #minmaxWH = cv2.minMaxLoc(weightHist)
#         #print "Mean weighted H",meanWH
#         #print "Dominant weighted H", minmaxWH
#         #hsvH = cv2.calcHist([greyres], [0], dstmaskC, [180], [0, 180])
#         #hsvS = cv2.calcHist([workFrameHSV], [1], dstmaskC, [255], [0, 255])
#         #hsvV = cv2.calcHist([workFrameHSV], [2], dstmaskC, [255], [0, 255])
#         #labH = cv2.calcHist([workFrameLAB], [0], dstmaskC, [100], [0, 100])
#         # if bright, is the color good for fox ?
#         #print "Dominant Color", minmaxH[3][1]
#         #print "Mean Color", meanHSV[0]
#         # is th saturation good for fox ?
#         #print "Mean Saturation" ,meanHSV[1]
#         #print "Dominant Saturation",minmaxS[3][1]
#         #minmaxV = cv2.minMaxLoc(hsvV)
#         #minmaxH = cv2.minMaxLoc(hsvH)
#         #minmaxL = cv2.minMaxLoc(labH)
#         # if low light, dont equalize !
#         greyres2 = cv2.equalizeHist(greyres3)
#         #greyresNoB = greyres2.copy()
#         # store values
#         meanGrey = cv2.mean(greyres3,dstmaskC)
#         minmaxGrey = cv2.minMaxLoc(hist_mask)
#         # percent of white ++++++++++++++++++++++++
#         print "Mean brightness", meanGrey
#         print "Dominant brightness", minmaxGrey
#         #greyres2 = greyres3        
#         print objV
#         #draw white contour
#         cv2.drawContours(greyres2,cnt,-1,255,2)
#         cv2.drawContours(workFramecp,cnt,-1,255,2)        
#         # bilateral filtering conserve edges
#         greyres1 = cv2.bilateralFilter(greyres2,9,75,75)
#         #greyres1 = cv2.blur(greyres2,(3,3)) #3,3 seems not bad
#         # adaptive thres
#         # if adult, use OTSU !!!!
#         #thh,greyres = cv2.threshold(
#         #    greyres1,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)        
#         greyres = cv2.adaptiveThreshold(
#             greyres1,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY_INV,11,2)
#         #greyres2 = greyres3
#         # erode
#         #greyres = cv2.erode(greyres1,ksegE,iterations = 1)
#         #open
#         retA = greyres
#         #retA = cv2.morphologyEx(greyres1, cv2.MORPH_OPEN, ksegO)
#         # equalize first
#         #greyres = cv2.equalizeHist(greyres1)
#         # adaptive equalization
#         #clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
#         #greyres = clahe.apply(greyres1)        
#         #greyres = cv2.convertScaleAbs(greyres1)
#         #threshA,retA = cv2.threshold(greyres,50,255,cv2.THRESH_BINARY)
#         #ret,threshold = cv2.threshold(
#         #greyres,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)        
#         #retA = cv2.adaptiveThreshold(greyres,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)        
#         # if not bright
#         #print "Mean saturation", meanHSV[1]
#         #print "Dominant Value",minmaxV[3][1]
#         #print "Dominant Hue",minmaxH[3][1]
#         #print "Dominant Lab",minmaxL[3][1]
#         # implement decisions !
#         # Is adult ? check for value channel        
#         # normalized RGB
#         # split
#         # create matrix
#         #norm = np.zeros((h,w,3),np.float32)
#         #B,G,R = cv2.split(workFrame)
#         #sum1 = B+G+R
#         #norm[:,:,0]=B/sum1*255.0
#         #norm[:,:,1]=G/sum1*255.0
#         #norm[:,:,2]=R/sum1*255.0
#         #norm_rgb = cv2.convertScaleAbs(norm)        
#         # split        
#         #hsvH = cv2.calcHist([workFrameHSV], [0], dstmaskC, [10], [0, 100])
#         #print hsvH
#         #rgbNH = cv2.calcHist([norm], [0,1,2], dstmaskC, [255,255,255], [0, 255])
#         #hsvS = cv2.calcHist([workFrameHSV], [1], dstmaskC, [256], [0, 256])
#         #print "hsv hue",hsvH[0]
#         #print "Min,Max H",cv2.minMaxLoc(hsvH)
#         #print "Min,Max S",cv2.minMaxLoc(hsvS)
#         #print "Min,Max Weighted",cv2.minMaxLoc(weighH)
#         # plot color histogram with openCV
#         #plt.figure()
#         #plt.plot(hsvH)
#         #plt.show()
#         # -==============================
#         # Color Histogram
#         # h = np.zeros((300,256,3))
#         # bins = np.arange(256).reshape(256,1)
#         # color = [ (255,0,0),(0,255,0),(0,0,255) ]
#         # for ch, col in enumerate(color):
#         #     hist_item = cv2.calcHist([workFrame],[ch],dstmaskC,[256],[0,255])
#         #     cv2.normalize(hist_item,hist_item,0,255,cv2.NORM_MINMAX)
#         #     hist=np.int32(np.around(hist_item))
#         #     pts = np.column_stack((bins,hist))
#         #     cv2.polylines(h,[pts],False,col)
#         # h=np.flipud(h)
#         #greyres = cv2.cvtColor(resim,cv2.COLOR_BGR2GRAY)
#         # ------------------------------------------
#         #print "Min,Max",cv2.GetMinMaxHistValue(hsvH)
#         #print "POST",cv2.mean(WFP,dstmaskC)
#         # -=============================================
#         #plt.hist(resim.ravel(),256,[0,256]);plt.show()
#         #cv2.namedWindow("blended",cv2.WINDOW_NORMAL)
#         # ------------------------------------------------------------
#         cv2.namedWindow("Gray",cv2.WND_PROP_FULLSCREEN)
#         #cv2.setWindowProperty(
#         #    "Gray", cv2.WND_PROP_FULLSCREEN, cv2.cv.CV_WINDOW_FULLSCREEN)
#         cv2.namedWindow("image",cv2.WINDOW_AUTOSIZE)
#         cv2.namedWindow("original",cv2.WINDOW_AUTOSIZE)
#         cv2.namedWindow("mask",cv2.WINDOW_NORMAL)
#         cv2.namedWindow("Edges",cv2.WND_PROP_FULLSCREEN)
#         cv2.setWindowProperty(
#             "Edges", cv2.WND_PROP_FULLSCREEN, cv2.cv.CV_WINDOW_FULLSCREEN)
#         cv2.moveWindow("mask",1500,300)
#         cv2.moveWindow("Gray",1500,200)
#         cv2.moveWindow("image",1900,200)
#         cv2.moveWindow("original",650,200)
#         cv2.moveWindow("Edges",200,200)
#         # --------
#         cv2.imshow('Gray',greyres2)
#         #cv2.imshow('Gray',edges)
#         cv2.imshow('image',workFramecp)
#         cv2.imshow('original',workFrame)
#         cv2.imshow('mask',out)
#         cv2.imshow('Edges',retA)
#         #cv2.imshow('Edges',retA)
#         #cv2.imshow('hsvH',hsvH)
#         #plt.figure()
#         #plt.plot(hsvH[0])
#         #plt.show()
#         # --------------
#         cv2.imwrite("mask.png",opened)
#         cv2.imwrite("segm.png",resim)
#         cv2.imwrite("work.png",workFrame)
#         cv2.imwrite("hist.png",h)
#         k = cv2.waitKey(0) & 0xff
#         cv2.destroyAllWindows()
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         # # -----------------------------------------------------
#         # write to csv values
#         #with open('valuescsv.csv','a') as output:
#         #    writer = csv.writer(output,lineterminator='\n')
#         #    writer.writerow([objV])
#         #valuescsv = open('valuescsv.csv','a')
#         #valuescsv.write(objV)
#         #valuescsv.close()
#         # store in vector all data
#         # ------
#         #grV = raw_input("enter value : ")
#         #objV = [os.path.basename(
#         #    imglist[si]),grV,minmaxH[3][1],meanHSV[0],
#         #        minmaxS[3][1],meanHSV[1],minmaxGrey[3][1],meanGrey[0]]
#         #objV = [os.path.basename(
#         #    imglist[si]),grV,meanB[0],meanG[0],
#         #        meanR[0],minmaxB[3][1],minmaxG[3][1],minmaxR[3][1],minmaxH[3][1],meanHSV[0],area]
#         #myfile = open('valuescsv3.csv', 'a')
#         #wr = csv.writer(myfile)
#         #wr.writerow(objV)


# # ############ ***************************************'
# # Analyse images to segment youngs
# # ####################################################
# # *****************************************************************
# kernelerY = np.ones((3,3),np.uint8) # opening kernel
# kernelerZ = np.ones((10,10),np.int8) # closing kernel 
# kerneler = np.ones((2,2),np.uint8) # erosion kernel
# # count monsters
# objcount = []
# areacount = []
# si = 1 # 729 (light) good for test young seg and 82 and 4300 (low light)
# # 823 impressionnant
# npts = []
# for i in range(len(maskslist[si:si+1])): # 739-750, great for diagnosis
#     objcountIm = []
#     print "Analysing",maskslist[si]
#     currentFrame = cv2.imread(imglist[si]) # load corresponding frame
#     resizimg1 = cv2.resize(
#             currentFrame,(0,0),fx=0.3,fy=0.3)# (0.3 works well)
#     workFrame  = resizimg1[80:-20,1:-10]    
#     workFrameHSV = cv2.cvtColor(workFrame, cv2.COLOR_BGR2HSV)
#     workFrameLAB = cv2.cvtColor(workFrame, cv2.COLOR_BGR2LAB)
#     B,G,R = cv2.split(workFrame)
#     Bp = (B - np.mean(B))/np.std(B)
#     Gp = (G - np.mean(G))/np.std(G)
#     Rp = (R - np.mean(R))/np.std(R)
#     # ---------------------------------------------------------
#     currentMask1 = cv2.imread(maskslist[si])
#     currentMask2 = currentMask1[80:-20,1:-10]
#     # Opening
#     opened = cv2.morphologyEx(currentMask2, cv2.MORPH_OPEN, kernelerY)
#     # find and draw contours
#     currentMaskOp = cv2.cvtColor(opened,cv2.COLOR_BGR2GRAY)
#     currentMask = cv2.convertScaleAbs(currentMaskOp)
#     contours,hye = cv2.findContours(currentMask.copy(),
#                                     cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
#     areas = [cv2.contourArea(c) for c in contours]
#     print "Number of monsters",len(contours)
#     print "Total Area",sum(areas)    
#     # ----------------------------------------------
#     # for evey contours,analyse corresponding blob
#     white = (255, 255, 255)
#     for cnt in contours:
#         objV = []
#         workFramecp = workFrame.copy() 
#         print "Area",cv2.contourArea(cnt)
#         area = cv2.contourArea(cnt)
#         dstmask = np.zeros(currentMask2.shape, dtype=np.uint8)
#         h, w = dstmask.shape[:2]        
#         cv2.drawContours(dstmask,cnt,-1,(255,255,255),-1)
#         mask = np.zeros((h+2, w+2), np.uint8)
#         # floodfill mask
#         seed_pt=None
#         cv2.floodFill(dstmask, mask,seed_pt, (255, 255, 255), 5, 5)
#         # invert image
#         dstmask = (255-dstmask)
#         #dstmaskC = cv2.convertScaleAbs(dstmask)
#         dstmaskC = cv2.cvtColor(dstmask,cv2.COLOR_BGR2GRAY)
#         resim = cv2.bitwise_and(workFrame,dstmask)
#         # display contours on original image
#         out = opened.copy()
#         cv2.drawContours(out,cnt,-1,255,2)
#         # Colors descriptors ----------------------------------------
#         # hist_mask = cv2.calcHist([workFrame],[0],dstmaskC,[256],[0,256])
#         hsv_hist = cv2.calcHist([workFrameHSV],
#                     [0,1,2],dstmaskC,[180,256,256],[0,180,0,256,0,256])
#         hsvH = cv2.calcHist([workFrameHSV], [0], dstmaskC, [180], [0, 180])
#         hsvS = cv2.calcHist([workFrameHSV], [1], dstmaskC, [255], [0, 255])
#         StB_hist = cv2.calcHist(
#             [Bp.astype('float32')],[0], dstmaskC, [100], [-10,10])
#         StG_hist = cv2.calcHist(
#             [Gp.astype('float32')],[0], dstmaskC, [100], [-10,10])
#         StR_hist = cv2.calcHist(
#             [Rp.astype('float32')],[0], dstmaskC, [100], [-10,10])
#         # store values
#         meanB = cv2.mean(Bp,dstmaskC)
#         meanG = cv2.mean(Gp,dstmaskC)
#         meanR = cv2.mean(Rp,dstmaskC)
#         minmaxB = cv2.minMaxLoc(StB_hist)
#         minmaxG = cv2.minMaxLoc(StG_hist)
#         minmaxR = cv2.minMaxLoc(StR_hist)
#         # print results
#         print "mean B G R :",meanB[0],meanG[0],meanR[0]
#         print "dominant B G R :",minmaxB[3][1],minmaxG[3][1],minmaxR[3][1]
#         meanHSV = cv2.mean(workFrameHSV,dstmaskC)
#         meanS = cv2.mean(workFrameHSV,dstmaskC)
#         minmaxS = cv2.minMaxLoc(hsvS)
#         minmaxH = cv2.minMaxLoc(hsvH)
#         # --- print results
#         # is it bright
#         # print "Mean brightness", meanHSV[2]
#         # print "Dominant brightness", minmaxV[3][1]
#         # # if bright, is the color good for fox ?
#         print "Dominant Color", minmaxH[3][1]
#         print "Mean Color", meanHSV[0]
#         print "Dominant Sat",minmaxS[3][1]
#         print "Mean Sat",meanHSV[1]
#         # Youngs segmentation ****************************************
#         # ------------------------------------------------------------
#         # implementation *********************************************
#         ksegO = np.ones((5,5),np.uint8) # opening kernel
#         ksegE = np.ones((1,1),np.uint8) # erode kernel        
#         # Convert to gray
#         greyres3 = cv2.cvtColor(resim,cv2.COLOR_BGR2GRAY)
#         # grey descriptors
#         hist_mask = cv2.calcHist([greyres3],[0],dstmaskC,[256],[0,256])
#         # if low light, dont equalize !
#         #greyres2 = greyres3
#         # if low light, use equalize
#         #greyres2 = cv2.equalizeHist(greyres3)
#         # if enough light, use CLAHE
#         clahe = cv2.createCLAHE(clipLimit=0.1, tileGridSize=(16,16))
#         greyres2 = clahe.apply(greyres3)
#         # store values
#         meanGrey = cv2.mean(greyres3,dstmaskC)
#         minmaxGrey = cv2.minMaxLoc(hist_mask)
#         # percent of white ++++++++++++++++++++++++
#         print "Mean brightness", meanGrey
#         print "Dominant brightness", minmaxGrey
#         #greyres2 = greyres3        
#         print objV
#         #draw white contour
#         cv2.drawContours(greyres2,cnt,-1,255,2)
#         cv2.drawContours(workFramecp,cnt,-1,255,2)        
#         # bilateral filtering conserve edges
#         greyres1 = cv2.bilateralFilter(greyres2,9,75,75)
#         #greyres1 = cv2.blur(greyres2,(3,3)) #3,3 seems not bad
#         # adaptive thres
#         # if adult, use OTSU !!!!
#         #thh,greyres = cv2.threshold(
#         #    greyres1,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)        
#         greyres = cv2.adaptiveThreshold(
#             greyres1,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY_INV,11,2)
#         # perform small erosion
#         greyresE = cv2.erode(greyres,kerneler,iterations = 1)
#         # find contours INSIDE main blob and count
#         contours2,hye2 = cv2.findContours(greyresE.copy(),
#                         cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
#         # loop through hye2
#         incount = []
#         for i in range(len(hye2[0])):
#             if hye2[0][i][3] ==1:
#                 print "count1"
#                 incount.append(1)
#             else:
#                 pass
#         objcountIm.append(len(incount))
#         # draw contours2
#         out2 = greyresE.copy()
#         cv2.drawContours(out2,contours2,-1,100,1)
#         print "N youngs ",len(contours2)
#         print hye2
#         retA = greyresE
#         # Display images
#         # -=============================================
#         #cv2.namedWindow("blended",cv2.WINDOW_NORMAL)
#         # ------------------------------------------------------------
#         cv2.namedWindow("Gray",cv2.WND_PROP_FULLSCREEN)
#         #cv2.setWindowProperty(
#         #    "Gray", cv2.WND_PROP_FULLSCREEN, cv2.cv.CV_WINDOW_FULLSCREEN)
#         cv2.namedWindow("image",cv2.WINDOW_AUTOSIZE)
#         cv2.namedWindow("original",cv2.WINDOW_AUTOSIZE)
#         cv2.namedWindow("mask",cv2.WINDOW_NORMAL)
#         cv2.namedWindow("Edges",cv2.WND_PROP_FULLSCREEN)
#         cv2.setWindowProperty(
#             "Edges", cv2.WND_PROP_FULLSCREEN, cv2.cv.CV_WINDOW_FULLSCREEN)
#         cv2.moveWindow("mask",1500,300)
#         cv2.moveWindow("Gray",1500,200)
#         cv2.moveWindow("image",1900,200)
#         cv2.moveWindow("original",650,200)
#         cv2.moveWindow("Edges",200,200)
#         # --------
#         cv2.imshow('Gray',greyres2)
#         #cv2.imshow('Gray',edges)
#         cv2.imshow('image',workFramecp)
#         cv2.imshow('original',workFrame)
#         cv2.imshow('mask',dstmask)
#         cv2.imshow('Edges',resim)
#         #cv2.imshow('Edges',retA)
#         #cv2.imshow('hsvH',hsvH)
#         #plt.figure()
#         #plt.plot(hsvH[0])
#         #plt.show()
#         # --------------
#         cv2.imwrite("mask.png",opened)
#         cv2.imwrite("segm.png",resim)
#         cv2.imwrite("work.png",workFrame)
#         cv2.imwrite("hist.png",h)
#         k = cv2.waitKey(0) & 0xff
#         cv2.destroyAllWindows()
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         # # -----------------------------------------------------
#         # write to csv values
#         #with open('valuescsv.csv','a') as output:
#         #    writer = csv.writer(output,lineterminator='\n')
#         #    writer.writerow([objV])
#         #valuescsv = open('valuescsv.csv','a')
#         #valuescsv.write(objV)
#         #valuescsv.close()
#         # store in vector all data
#         # ------
#         #grV = raw_input("enter value : ")
#         #objV = [os.path.basename(
#         #    imglist[si]),grV,minmaxH[3][1],meanHSV[0],
#         #        minmaxS[3][1],meanHSV[1],minmaxGrey[3][1],meanGrey[0]]
#         #objV = [os.path.basename(
#         #    imglist[si]),grV,meanB[0],meanG[0],
#         #        meanR[0],minmaxB[3][1],minmaxG[3][1],minmaxR[3][1],minmaxH[3][1],meanHSV[0],area]
#         #myfile = open('valuescsv3.csv', 'a')
#         #wr = csv.writer(myfile)
#         #wr.writerow(objV)
#     print objcountIm
#     objcount.append(sum(objcountIm))
#     print "objcount",objcount
        
# # once satified with tests, proceed.

# # Count monsters +++++++++++++++++++++++++++++++++++++++++++++++++++
# # first, count without area condition. This is the base count.
# ######################################################################
# #kernelerZ = np.ones((10,10),np.int8) # closing kernel 
# #kerneler = np.ones((5,5),np.uint8) # erosion kernel
# # count monsters
# objcount = []
# areacount = []
# for i in range(len(maskslist)):
#     kernelerY = np.ones((1,1),np.uint8) # opening kernel
#     print "Analysing",maskslist[i]
#     #--------------------------------------
#     currentMask1 = cv2.imread(maskslist[i])
#     # remove unwanted regions
#     currentMask2 = currentMask1[80:-20,1:-10]
#     # Opening
#     opened = cv2.morphologyEx(currentMask2, cv2.MORPH_OPEN, kernelerY)
#     #opened = currentMask2
#     # closing
#     #closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernelerZ)
#     # find and draw contours
#     currentMask3 = cv2.cvtColor(opened,cv2.COLOR_BGR2GRAY)
#     currentMask = cv2.convertScaleAbs(currentMask3)
#     #contours,_ = cv2.findContours(currentMask,
#     #                              cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
#     contours,hye = cv2.findContours(currentMask.copy(),
#                                     cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#     areas = [cv2.contourArea(c) for c in contours]
#     areastmp = sum(areas)
#     contourstmp = len(contours)
#     # big areas sum == problem
#     if areastmp > 50000:
#         objcount.append(1000)
#         areacount.append(1000)
#     else:
#         if contourstmp > 15: # or 10...
#             kernelerY = np.ones((10,10),np.uint8) # opening kernel
#             opened = cv2.morphologyEx(currentMask2, cv2.MORPH_OPEN, kernelerY)
#             currentMask3 = cv2.cvtColor(opened,cv2.COLOR_BGR2GRAY)
#             currentMask = cv2.convertScaleAbs(currentMask3)
#             contours,hye = cv2.findContours(currentMask.copy(),
#                                     cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#             areas = [cv2.contourArea(c) for c in contours]
#             objcount.append(len(contours))
#             areacount.append(sum(areas))
#         else:
#             kernelerY = np.ones((3,3),np.uint8) # opening kernel
#             opened = cv2.morphologyEx(currentMask2, cv2.MORPH_OPEN, kernelerY)
#             currentMask3 = cv2.cvtColor(opened,cv2.COLOR_BGR2GRAY)
#             currentMask = cv2.convertScaleAbs(currentMask3)
#             contours,hye = cv2.findContours(currentMask.copy(),
#                                     cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#             areas = [cv2.contourArea(c) for c in contours]
#             objcount.append(len(contours))
#             areacount.append(sum(areas))
#         #areacount.append(sum(areas))
#         #objcount.append(len(areas))
#     # display contours and original image
#     #cv2.namedWindow("opened",cv2.WINDOW_NORMAL)
#     #cv2.imshow('opened',eroded)
#     #cv2.imshow('opened',out)
#     #k = cv2.waitKey(0) & 0xff
#     # cv2.destroyAllWindows()
#     # cv2.waitKey(1) & 0xff
#     # cv2.waitKey(1) & 0xff
#     # cv2.waitKey(1) & 0xff
#     # cv2.waitKey(1) & 0xff    
# print "DONE"

# # Count monsters 2 +++++++++++++++++++++++++++++++++++++++++++++++++++
# # Count with area condition
# ######################################################################
# #kernelerZ = np.ones((10,10),np.int8) # closing kernel 
# #kerneler = np.ones((5,5),np.uint8) # erosion kernel
# # count monsters
# objcount = []
# areacount = []
# for i in range(len(maskslist)):
#     kernelerY = np.ones((3,3),np.uint8) # opening kernel
#     print "Analysing",maskslist[i]
#     #--------------------------------------
#     currentMask1 = cv2.imread(maskslist[i])
#     # remove unwanted regions
#     currentMask2 = currentMask1[80:-20,1:-10]
#     # Opening
#     opened = cv2.morphologyEx(currentMask2, cv2.MORPH_OPEN, kernelerY)
#     #opened = currentMask2
#     # closing
#     #closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernelerZ)
#     # find and draw contours
#     currentMask3 = cv2.cvtColor(opened,cv2.COLOR_BGR2GRAY)
#     currentMask = cv2.convertScaleAbs(currentMask3)
#     #contours,_ = cv2.findContours(currentMask,
#     #                              cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
#     contours,hye = cv2.findContours(currentMask.copy(),
#                                     cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#     areas = [cv2.contourArea(c) for c in contours]
#     areastmp = sum(areas)
#     contourstmp = len(contours)
#     # big areas sum == problem
#     if areastmp > 50000:
#         objcount.append(1000)
#         areacount.append(1000)
#     else:
#         blobtmp = []
#         for c in contours: # reiterate to implement young seg
#             # measure area
#             area = cv2.contourArea(c)
#             if area < 150: # original 150
#                 pass
#             else:
#                 blobtmp.append(1)
#         objcount.append(len(blobtmp))
#         areacount.append(sum(areas))
# print "Done"
# ####################################################################


# # Count monsters 3 +++++++++++++++++++++++++++++++++++++++++++++++++++
# # Count with area condition and young segmentation
# def segyoungs():
#     ##############################################################
#     # Youngs segmentation ****************************************
#     # ------------------------------------------------------------
#     # implementation *********************************************
#     ksegO = np.ones((5,5),np.uint8) # opening kernel
#     ksegE = np.ones((1,1),np.uint8) # erode kernel        
#     # Convert to gray
#     greyres3 = cv2.cvtColor(resim,cv2.COLOR_BGR2GRAY)
#     # grey descriptors
#     hist_mask = cv2.calcHist([greyres3],[0],dstmaskC,[256],[0,256])
#     # if low light, dont equalize !
#     #greyres2 = greyres3
#     # if low light, use equalize
#     #greyres2 = cv2.equalizeHist(greyres3)
#     # if enough light, use CLAHE
#     clahe = cv2.createCLAHE(clipLimit=0.1, tileGridSize=(16,16))
#     greyres2 = clahe.apply(greyres3)
#     # store values
#     meanGrey = cv2.mean(greyres3,dstmaskC)
#     minmaxGrey = cv2.minMaxLoc(hist_mask)
#     # percent of white ++++++++++++++++++++++++
#     print "Mean brightness", meanGrey
#     print "Dominant brightness", minmaxGrey
#     #greyres2 = greyres3        
#     #print objV
#     #draw white contour
#     cv2.drawContours(greyres2,c,-1,255,2)
#     cv2.drawContours(workFramecp,c,-1,255,2)        
#     # bilateral filtering conserve edges
#     greyres1 = cv2.bilateralFilter(greyres2,9,75,75)
#     #greyres1 = cv2.blur(greyres2,(3,3)) #3,3 seems not bad
#     # adaptive thres
#     # if adult, use OTSU !!!!
#     #thh,greyres = cv2.threshold(
#     #    greyres1,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)        
#     greyres = cv2.adaptiveThreshold(
#         greyres1,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY_INV,11,2)
#     # perform small erosion
#     greyresE = cv2.erode(greyres,kerneler,iterations = 1)
#     # find contours INSIDE main blob and count
#     contours2,hye2 = cv2.findContours(greyresE.copy(),
#                                       cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
#     # loop through hyerarchy
#     incount = []
#     for i in range(len(hye2[0])):
#         if hye2[0][i][3] ==1:
#             print "count1"
#             incount.append(1)
#         else:
#             pass
#     objcountIm.append(len(incount))
#     # draw contours2
#     out2 = greyresE.copy()
#     cv2.drawContours(out2,contours2,-1,100,1)
#     print "N youngs ",len(contours2)
#     print hye2

# ######################################################################
# #kernelerZ = np.ones((10,10),np.int8) # closing kernel 
# #kerneler = np.ones((5,5),np.uint8) # erosion kernel
# # count monsters
# kernelerY = np.ones((3,3),np.uint8) # opening kernel
# kernelerZ = np.ones((10,10),np.int8) # closing kernel 
# kerneler = np.ones((2,2),np.uint8) # erosion kernel
# objcount = []
# areacount = []
# si = 729 # 729 (light) good for test young seg and 82 and 4300 (low light)
# for i in range(len(maskslist[si:si+1])): # 739-750, great for diagnosis
# #for i in range(len(maskslist)):
#     print "Analysing",maskslist[si]
#     currentFrame = cv2.imread(imglist[si]) # load corresponding frame
#     resizimg1 = cv2.resize(
#             currentFrame,(0,0),fx=0.3,fy=0.3)# (0.3 works well)
#     workFrame  = resizimg1[80:-20,1:-10]    
#     #--------------------------------------
#     currentMask1 = cv2.imread(maskslist[si])
#     # remove unwanted regions
#     currentMask2 = currentMask1[80:-20,1:-10]
#     # Opening
#     opened = cv2.morphologyEx(currentMask2, cv2.MORPH_OPEN, kernelerY)
#     currentMaskOp = cv2.cvtColor(opened,cv2.COLOR_BGR2GRAY)
#     currentMask = cv2.convertScaleAbs(currentMaskOp)
#     # find contours to get rough analyse first
#     contours,hye = cv2.findContours(currentMask.copy(),
#                                     cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#     areas = [cv2.contourArea(c) for c in contours]
#     areastmp = sum(areas)
#     contourstmp = len(contours)
#     # Perform bitwise operation =====================================
#     workFramecp = workFrame.copy()
#     dstmask = np.zeros(currentMask2.shape, dtype=np.uint8)
#     h, w = dstmask.shape[:2]
#     cv2.drawContours(dstmask,c,-1,(255,255,255),-1)
#     mask = np.zeros((h+2, w+2), np.uint8)
#     # floodfill mask
#     seed_pt=None
#     cv2.floodFill(dstmask, mask,seed_pt, (255, 255, 255), 5, 5)
#     # invert image
#     dstmask = (255-dstmask)
#     #dstmaskC = cv2.convertScaleAbs(dstmask)
#     dstmaskC = cv2.cvtColor(dstmask,cv2.COLOR_BGR2GRAY)
#     resim = cv2.bitwise_and(workFrame,dstmask)
#     # End bitwise operation for mask ===================================
#     # big total areas sum == problem, probably light blast
#     if areastmp > 50000:
#         print "areas too big, light or stability problem"
#         objcount.append(1000)
#         areacount.append(1000)
#     else:
#         blobtmp = []
#         print "Analysing and segmenting blobs if appropriate"
#         for cnt in contours: # 
#             # measure area
#             area = cv2.contourArea(c)
#             if area > 150: # original 150
#                 # call segment youngs function
#                 segyoungs()
#             else:
#                 pass                
#         blobtmp.append(1)
#         objcount.append(len(blobtmp))
#         areacount.append(sum(areas))
# print "Done"
# ####################################################################

# # correll with camille count
# # load camille data, one file -----------------------------
# frame = pd.DataFrame()

# xl = pd.ExcelFile("/home/edevost/Renards2014/Phase2/DataCamilleComplete/watchs/2010/tab_2010_Fox207.xlsx")

# #xl = pd.ExcelFile("/home/edevost/Renards2014/Phase2/DataCamilleComplete/watchs/2010/tab_2012_Fox134.xlsx")

# #xl = pd.ExcelFile("/home/edevost/Renards2014/Phase2/DataCamilleComplete/watchs/2012/tab_2012_FOX107.xlsx")

# dfCt = xl.parse(0)
# dfC = dfCt.ix[:,['Photo','Annee','Taniere','AM','ANM','J']] # F134 JNM
# print "DONE"

# # for 2012 fox 107 ############
# dfCS = dfC[207:207+1689]

# dfCS = dfC[207:207+200]
 
# # select good section
# #for 2010-Fox207 100801.F207.DB25/100RECNX/
# #dfCS = dfC[715:715+746]
# #dfCS = dfC[715:715+5063]
# dfCS = dfC[715:715+4600]
# #dfCS = dfC[715:715+5050]
# # ---------------------------

# # for 2010 fox 134-100701-cam1 (JNM)
# #dfCS = dfC[0:2475]
# #dfCS = dfC[0:2300]
# #dfCS = dfC[0:100]
# #print dfCS

# # Add a TotAn (Total animaux) in 8th columns of dataframe
# columns2 = ['AM','ANM','J']
# dfCS['TotAn'] = dfCS[columns2].sum(axis=1)
# print "done"
# # add presence absence data
# dfCS['PresAbs'] = (dfCS['TotAn']>0).astype(int)
# print dfCS

# # Add a TotAn (Total animaux) in 8th columns of dataframe
# #columns2 = ['AM','ANM','JNM']
# #dfCS['TotAn'] = dfCS[columns2].sum(axis=1)
# #print "done"
# # add presence absence data
# #dfCS['PresAbs'] = (dfCS['TotAn']>0).astype(int)
# # create results dataframe
# #camC = dfC['TotAn'] we have to load dfC (see beginning of file)
# #dfC1 = dfCS[0:2475]
# #camC = list(dfC1['JNM'])
# #camC = camC1[0:5059]
# #camC = [0:5063]
# # add count datas in dataframe
# #dfCS['SoftC'] = objcount[0:5049]
# # read ycount from file
# my_data = np.genfromtxt('softcountYF2010-207-4600.csv', delimiter=',')
# ycountT = map(int,my_data)
# #ycountT = ycount
# dfCS['SoftC'] = ycountT
# print dfCS
# # add presence absence for visual count
# presab = []
# # create a presence absence vector fo objcount
# for item in ycountT:
# #for item in objcount:    
#     if item != 0:
#         presab.append(1)
#     else:
#         presab.append(0)
# print "DONE"
# # add to dataframe
# dfCS['SoftPresAbs'] = presab
# # Remove camera fall
# dfCS = dfCS[:4970]

# # Remove 1000 values
# dfCS1 = dfCS[dfCS['SoftC']==1000]
# dfCS2 = dfCS[dfCS['SoftC']!=1000]
# # remove high count
# # remove firsts five images
# dfCS3 = dfCS2[5:]

# dfCS3 = dfCS2[dfCS2['SoftC'] < 50]

# #dfCS3 = dfCS2
# # Remove Visual count 0 class
# #dfCS2 = dfCS[dfCS['JNM']!=0]
# #dfCS2 = dfCS1

# # -----------------------------------------------
# #### see zero counts Camille with large count software
# dfCS0 = dfCS[dfCS['JNM']==0]
# #### Query 0 count for me and count for C
# dfCSM0 = dfCS2[dfCS2['SoftC']==0]
# # --------------------------------------------------

# # Create lists for corellation
# camC1 = list(dfCS3['J'])
# objc = list(dfCS3['SoftC'])
               
# slopeO, interceptO, r_valueO, p_valueO, std_errO = linregress(camC1,objc)
# print "r squared count = ",r_valueO**2
# r_valueO = r_valueO**2
# print "slope",slopeO
# print "p-value",p_valueO


# # plot raw corellation
# plt.scatter(camC1,objc)
# #plt.title('Obj count: erode = %s, dilate = %s, thres = %s'%(er,dil,thres))
# plt.xlabel('Camille count')
# plt.ylabel('Software indice')
# #pylab.savefig(resultsdir + 'ObjCount-' + str(count) + '.pdf',bbox_inches='tight')
# plt.show()

# # plot mean with sd
# dfCS3.pivot_table(rows='J',aggfunc={"SoftC":[np.mean,np.std]})

# # number of images to show with RS
# imgRS = dfCS3[dfCS3['SoftC'] > 15 ]

# print len(dfCS3[dfCS3['SoftC'] >= 15 ])

# # see where mismatches occurs
# dfCS3['MissM'] = dfCS3['SoftC']-dfCS3['J']

# # select highest missmatch
# print dfCS3[dfCS3['MissM']>=5] # 229 overestimated missmatch)
# print len(dfCS3[dfCS3['MissM']>=5]) # 229 overestimated missmatch)
 
# print dfCS3[dfCS3['MissM']<=-5] # 488 underestimated missmatch)
# print len(dfCS3[dfCS3['MissM']<=-5]) # 488 underestimated missmatch)

# # select highest missmatch
# print dfCS3[dfCS3['MissM']>=10] # 40 highly overestimated missmatch

# print dfCS3[dfCS3['MissM']<=-10] # 7 highly underestimated missmatch



# # select Camcount 0
# print dfCSred[dfCSred['TotAn']==0]

# # select softcount 0
# # select Camcount 0
# print dfCSred[dfCSred['SoftC']==0]

# tmp1 = dfCSred[dfCSred['SoftC']==1]
# print tmp1

# print tmp1[tmp1['MissM']<-3]
# ###################################################





# # Test 5% images
# dfCS3sort = dfCS3.sort(['SoftC'])

# dfperc = int(len(dfCS3sort)*0.1)

# pc5 =  dfCS3sort[int(len(dfCS3sort)-dfperc):]
# print pc5

# RScamille = max(dfCS3['JNM'])

# print pc5[pc5['JNM']==RScamille]

# print pc5[pc5['JNM']==5]

# # 438, opening 10,10 et closing 10,10
# ######### ***************************************************

# ###############################################

# plt.scatter(camC,areacount)
# #plt.title('Obj count: erode = %s, dilate = %s, thres = %s'%(er,dil,thres))
# plt.xlabel('Camille count')
# plt.ylabel('Software indice')
# #pylab.savefig(resultsdir + 'ObjCount-' + str(count) + '.pdf',bbox_inches='tight')
# plt.show()
# slopeO, interceptO, r_valueO, p_valueO, std_errO = linregress(camC1,areacount)
# print "r squared count = ",r_valueO**2
# r_valueO = r_valueO**2



# # evaluate presence absence success
# listCam = list(dfC1['PresAbs'])
# listClass = list(dfC1['SoftPresAbs'])
# matchlist = []
# for i in range(len(listClass)):
#     #print listClass[i] == listCam[i]
#     matchlist.append(listClass[i] == listCam[i])
# print "Overal success",sum(matchlist)/float(len(matchlist))
# Ovsucc = sum(matchlist)/float(len(matchlist))

# reddf = dfC1[dfC1['PresAbs']== 1]
# listCam2 = list(reddf['PresAbs'])
# listClass2 = list(reddf['SoftPresAbs'])
# matchlist2 = []    
# for i in range(len(listClass2)):
#     #print listClass[i] == listCam[i]
#     matchlist2.append(listClass2[i] == listCam2[i])    
# print "Fox success",sum(matchlist2)/float(len(matchlist2))


# ######################################################################

# # this is a test for one sequence (sequence 100)
# sequences = [100]
# for sequence in sequences:
#     print impg[sequence]
#     # sous groupe impg
#     nseq1 = impg[sequence]/25
#     nseqm = impg[sequence]%25
#     newseq = [25]*nseqm
#     newseq.append(nseqm)
#     print "splitting impg", newseq


#     for x in range(len(newseq)):
#         print x
#         print newseq[x]
#         print impg[sequence]
#         print "Analysing sequence ",sequence
#         print "Analysing splitted seq ",newseq[x]
                   
#         currentFrame = cv2.imread(imglist[image + int(sum(impg[0:sequence]))+x])
#         print "img",imglist[image + int(sum(impg[0:sequence]))+x]
        
#         for sequence in range(len(impg)):
#         print "Analysing sequence ",sequence+1 ### xx
#         # resize images
#         for image in range(impg[sequence]):
#             #print "image",image
#             currentFrame = cv2.imread(imglist[image + int(sum(impg[0:sequence]))])
#             print "img",imglist[image + int(sum(impg[0:sequence]))]
#             #print "Resizing",image+1        
#             resizimg = cv2.resize(
#                 currentFrame,(0,0),fx=0.3,fy=0.3)
#             # save resized frame to temp dir
#             cv2.imwrite(os.path.join(temp1,
#                 os.path.basename(imglist[image + int(sum(
#                     impg[0:sequence]))])[0:-4]+".jpg"), resizimg)
#         # call c++ executable to estimate background
#         os.system(cppcom)
#         # call c++ executable to subtract background
#         # copy background    
#         os.system(cppfg)    
#         # clean tmpdir
#         for the_file in os.listdir(temp1):
#             file_path = os.path.join(temp1, the_file)
#             try:
#                 if os.path.isfile(file_path):
#                     os.unlink(file_path)
#             #elif os.path.isdir(file_path): shutil.rmtree(file_path)
#             except Exception, e:
#                 print e

    
# currentMask = []
# currentMask2 = []
# currentMask1 = []
# currentMask3 = []


# # test to count with running avg on a 70 seq images
# # ======================================================================
# # get wante seq (2010 fox 207), 70 imgs with the only one image with realRS
# start = 4150
# stop = 4220
# # get slice
# #start =  sum(impg[:idx])
# #stop = sum(impg[:idx+1])

# sample = imglist[start:stop]

# # read frames
# frames = []
# for frame in range(len(sample)):
#     frames.extend(cv2.imread(sample[frame]))
#     print "done"



# alpha = (1/float(np.log(200**1.4))-0.105)
# totarea = []
# nobj = []
# impg2 = [int(70)]
# kernelerY = np.ones((5,5),np.uint8) # opening kernel 
# thres=30
# for z in range(len(impg2)):
#     # detect bg
#     # get the first image as bst
#     accu = np.float32(cv2.imread(sample[int(sum(impg2[0:z]))]))
#     print "Sequence No:",z,"/",len(impg2)
#     for y in range(impg2[0]):
#     #for y in range(len(sample)):
#         currentFrame = cv2.imread(sample[y + int(sum(impg2[0:z]))])
#         # third argument of next line is alpha (weight of the input image)
#         currentBG = cv2.accumulateWeighted(currentFrame,accu,0.02)
#         currentBG = cv2.convertScaleAbs(accu)
#         if y == impg2[0]-1:
#         #if y==len(sample)-1:
#             print "image ",y
#             # append bgtmp image in background list
#             bgx = currentBG
#             print "Background successfully estimated"
#             # display bg
#             #img = cv2.imread(sample[-1])
#             # cv2.namedWindow("bg",cv2.WINDOW_NORMAL)
#             # cv2.imshow('bg',bgx)
#             # k = cv2.waitKey(0) & 0xff
#             # cv2.destroyAllWindows()
#             # cv2.waitKey(1) & 0xff
#             # cv2.waitKey(1) & 0xff
#             # cv2.waitKey(1) & 0xff
#             # cv2.waitKey(1) & 0xff
#         else:
#             print "image ",y

#         # count our little fiends
#     for image in range(impg2[0]):
#         # remove detected bg
#         print "counting monsters"
#         #bg = cv2.imread(sample[102])
#         currentFrame = cv2.imread(sample[image])
#         # substract bg
#         img_rescol = cv2.absdiff(currentFrame,bgx)
#         # crop useless top of images
#         crop = img_rescol[200:,]
#         # test sequence 1 =============================================
#         gray_img = cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY)
#         # thresholding
#         th2,im_bw = cv2.threshold(gray_img,thres,255,cv2.THRESH_BINARY)
#         #im_bw1 = cv2.adaptiveThreshold(gray_img,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#         #                               cv2.THRESH_BINARY_INV,11,5)
#         #ret2,im_bw = cv2.threshold(gray_img,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
#         # blurrr genre
#         #kernel = np.ones((15,15),np.float32)/25
#         #dst = cv2.filter2D(gray_img,-1,kernel)
#         #ret2,im_bw2 = cv2.threshold(im_bw1,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
#         # opening
#         opened = cv2.morphologyEx(im_bw, cv2.MORPH_OPEN, kernelerY)
#         contours, _ = cv2.findContours(opened,
#                         cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
#         areas = [cv2.contourArea(c) for c in contours]
#         totareatmp = sum(areas)
#         nobjtmp = len(areas)
#         totarea.append(totareatmp)
#         nobj.append(nobjtmp)
# print "DONE"

# #check corell


# slopeO, interceptO, r_valueO, p_valueO, std_errO = linregress(camC,nobj)
# print "r squared count = ",r_valueO**2
# r_valueO = r_valueO**2


# plt.scatter(camC,nobj)
# #plt.title('Obj count: erode = %s, dilate = %s, thres = %s'%(er,dil,thres))
# plt.xlabel('Camille count')
# plt.ylabel('Software indice')
# #pylab.savefig(resultsdir + 'ObjCount-' + str(count) + '.pdf',bbox_inches='tight')
# plt.show()

            
    
# # display bg
# #img = cv2.imread(sample[-1])
# cv2.namedWindow("bg",cv2.WINDOW_NORMAL)
# cv2.imshow('bg',bgx)
# k = cv2.waitKey(0) & 0xff
# cv2.destroyAllWindows()
# cv2.waitKey(1) & 0xff
# cv2.waitKey(1) & 0xff
# cv2.waitKey(1) & 0xff
# cv2.waitKey(1) & 0xff

# kernelerY = np.ones((5,5),np.uint8) # opening kernel 
# thresh=30

# # get background
# bg = cv2.imread("/home/edevost/Renards2014/Phase2/NewBGest/background_estimation_code/code/newbg70-3.jpg")

# #bg = cv2.imread(sample[102])
# currentFrame = cv2.imread("/home/edevost/Renards2014/Phase2/NewBGest/test1/seq1/Resized-Resized-0004.jpg")
# # substract bg
# img_rescol = cv2.absdiff(currentFrame,bg)
# # display image
# #cv2.namedWindow("adapt",cv2.WINDOW_NORMAL)
# cv2.namedWindow("rescol",cv2.WINDOW_NORMAL)
# cv2.imshow('rescol',img_rescol)
# k = cv2.waitKey(0) & 0xff
# cv2.destroyAllWindows()
# cv2.waitKey(1) & 0xff
# cv2.waitKey(1) & 0xff
# cv2.waitKey(1) & 0xff
# cv2.waitKey(1) & 0xff


# thres = 70
# # crop useless top of images
# crop = img_rescol[20:,]
# # test sequence 1 =============================================
# gray_img = cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY)
# # thresholding
# th2,im_bw2 = cv2.threshold(gray_img,thres,255,cv2.THRESH_BINARY)
# #im_bw2 = cv2.adaptiveThreshold(gray_img,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
# #                               cv2.THRESH_BINARY_INV,11,5)
# # blurrr genre
# #kernel = np.ones((15,15),np.float32)/25
# #dst = cv2.filter2D(gray_img,-1,kernel)
# #ret2,im_bw2 = cv2.threshold(gray_img,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
# # opening
# #opened = cv2.morphologyEx(im_bw, cv2.MORPH_OPEN, kernelerY)
# # display image
# #cv2.namedWindow("adapt",cv2.WINDOW_NORMAL)
# cv2.namedWindow("otsu",cv2.WINDOW_NORMAL)
# #cv2.imshow('adapt',im_bw1)
# #cv2.imshow('otsu',im_bw2)
# #cv2.imshow('frame',crop)
# cv2.imshow('otsu',im_bw2)
# k = cv2.waitKey(0) & 0xff
# cv2.destroyAllWindows()
# cv2.waitKey(1) & 0xff
# cv2.waitKey(1) & 0xff
# cv2.waitKey(1) & 0xff
# cv2.waitKey(1) & 0xff
# # ================================================================

# #gray_img = np.float32(cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY))

# im_bw1 = cv2.adaptiveThreshold(gray_img,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#                                cv2.THRESH_BINARY_INV,11,5)

# blur = cv2.GaussianBlur(gray_img,(5,5),0)

# #th2,slight = cv2.threshold(gray_img,50,255,cv2.THRESH_BINARY)

# ## Kernel opening
# kernelerY = np.ones((5,5),np.uint8) # opening kernel for high activity
# ## Kernel closing
# kernelcY = np.ones((5,5),np.uint8) # closing kernel for high activity

# opened = cv2.morphologyEx(im_bw2, cv2.MORPH_OPEN, kernelerY)

# # Closing
# closed = cv2.morphologyEx(im_bw2, cv2.MORPH_CLOSE, kernelcY)


# # Thresholding ###################################################
# #im_bw = cv2.threshold(gray_img, thresh, 255, cv2.THRESH_BINARY)[1]

# # find contours test
# contours, _ = cv2.findContours(gray_img,
#                             cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

# cv2.drawContours(gray_img, contours, -1, (0,255,0), 3)

# # display image
# #cv2.namedWindow("adapt",cv2.WINDOW_NORMAL)
# cv2.namedWindow("otsu",cv2.WINDOW_NORMAL)
# #cv2.imshow('adapt',im_bw1)
# #cv2.imshow('otsu',im_bw2)
# #cv2.imshow('frame',crop)
# cv2.imshow('otsu',im_bw2)
# k = cv2.waitKey(0) & 0xff
# cv2.destroyAllWindows()
# cv2.waitKey(1) & 0xff
# cv2.waitKey(1) & 0xff
# cv2.waitKey(1) & 0xff
# cv2.waitKey(1) & 0xff



# # check sqi manque
# resmasks1 = "/run/media/edevost/iomega1/MasksTests/2010-F207-01/temp11/"


# # load results and perform count
# maskslist1 = glob.glob(resmasks1 + "/*.png")
# maskslist1.sort()
# # remove first 3
# maskslist1 = maskslist1[3:]
# print maskslist1[0]


# maskslist2 = glob.glob(resmasks2 + "/*.png")
# maskslist2.sort()
# # remove first 3
# maskslist2 = maskslist2[4:]
# print maskslist2[0]

# one = []
# for i in maskslist1:
#     one.append(os.path.basename(i)[:-4])

# two = []
# for i in imglist:
#     two.append(os.path.basename(i)[:-4])


# for i in range(len(one)):
#     if one[i] == two[i]:
#         pass
#     else:
#         print one[i],two[i]
        
# # function to compute best maxgap
# tempimpg1 = []
# for cnt in range(4):
#     for x in range(len(impg)):
#         #print impg[x]
#         if impg[x] <= 30:
#             tempimpg1.append(impg[x])
#         elif 30 < impg[x] < 100:
#             #print impg[x]
#             tempimpg1.append(impg[x]-25)
#             tempimpg1.append(impg[x]-(impg[x]-25))
#         elif 100 <= impg[x] <= 200:
#             #print impg[x]
#             tempimpg1.append(impg[x]-75)
#             tempimpg1.append(impg[x]-(impg[x]-75))
#         else:
#             tempimpg1.append(impg[x]-100)
#             tempimpg1.append(impg[x]-(impg[x]-100))

#     impg = tempimpg1
#     tempimpg1 = []

# # function to compute best maxgap
# tempimpg2 = []
# for x in range(len(tempimpg1)):
#     #print impg[x]
#     if tempimpg1[x] <= 30:
#         tempimpg.append(tempimpg1[x])
#     elif 30 < tempimpg1[x] < 100:
#         #print impg[x]
#         tempimpg.append(tempimpg1[x]-30)
#         tempimpg.append(tempimpg1[x]-(tempimpg1[x]-30))
#     elif 100 <= tempimpg1[x] <= 200:
#         #print impg[x]
#         tempimpg.append(tempimpg1[x]-75)
#         tempimpg.append(tempimpg1[x]-(tempimpg1[x]-75))
#     else:
#         tempimpg.append(tempimpg1[x]-100)
#         tempimpg.append(tempimpg1[x]-(tempimpg1[x]-100))

#                 # for evey contours,extract corresponding blob
#     white = (255, 255, 255)
#     dstmask = np.zeros(currentMask2.shape, dtype=np.uint8)
#     for cnt in contours:
#         dstmask = np.zeros(currentMask2.shape, dtype=np.uint8)
#         cv2.fillPoly(dstmask,cnt,white)
#         resim = cv2.bitwise_and(workFrame,dstmask)
#         # display contours and original image
#         cv2.namedWindow("blended",cv2.WINDOW_AUTOSIZE)
#         cv2.moveWindow("blended",1500,200)
#         cv2.imshow('blended',resim)
#         k = cv2.waitKey(0) & 0xff
#         cv2.destroyAllWindows()
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
        
#         # ------------------------------------------------------
#         out = np.zeros_like(currentMask.copy()).astype('uint8')
#         cv2.drawContours(out,contours,-1,(255,255,55),3)
#         # if sum area too big, problem with frame
#         # blend images
#         blended = cv2.addWeighted(workFrame,1,opened,0.8,0)    
#         # display contours and original image
#         cv2.namedWindow("blended",cv2.WINDOW_AUTOSIZE)
#         cv2.moveWindow("blended",1500,200)
#         cv2.imshow('blended',out)
#         k = cv2.waitKey(0) & 0xff
#         cv2.destroyAllWindows()
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff
#         cv2.waitKey(1) & 0xff    
#     #eroded = cv2.erode(opened,kerneler,iterations = 1)
#     if sum(areas) > 20000:
#         objcount.append(0)
#         areacount.append(0)
#     else:
#         # cv2.drawContours(out,contours,-1,(0,255,0),2)
#         #print "sum areas: ",sum(areas)
#         #print "Nobj", len(areas)
#         areacount.append(sum(areas))
#         objcount.append(len(areas))
#     # display contours and original image
    
#     #cv2.namedWindow("opened",cv2.WINDOW_NORMAL)
#     #cv2.imshow('opened',eroded)
#     #cv2.imshow('opened',out)
#     #k = cv2.waitKey(0) & 0xff
#     # cv2.destroyAllWindows()
#     # cv2.waitKey(1) & 0xff
#     # cv2.waitKey(1) & 0xff
#     # cv2.waitKey(1) & 0xff
#     # cv2.waitKey(1) & 0xff    
# print "DONE"

# # posterize image --------------------------------------
#     # n = 4    # Number of levels of quantization
#     # indices = np.arange(0,256)   # List of all colors 
#     # divider = np.linspace(0,255,n+1)[1] # we get a divider
#     # quantiz = np.int0(np.linspace(0,255,n)) # we get quantization colors
#     # color_levels = np.clip(np.int0(indices/divider),0,n-1) # color levels 0,1,2..
#     # palette = quantiz[color_levels] # Creating the palette
#     # WFP = workFrame.copy()
#     # WFP = palette[WFP]  # Applying palette on image
#     # WFP = cv2.convertScaleAbs(WFP) # Converting image back to uint8    
#     # --------------------------------------------------
#     #workFramePost = workFrame
#     #workFramePost[workFramePost >= 128]= 255
#     #workFramePost[workFramePost < 128] = 0
#     #--------------------------------------
