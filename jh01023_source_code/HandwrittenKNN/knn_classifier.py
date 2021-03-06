import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from skimage.segmentation import clear_border
from skimage.morphology import label
from skimage.measure import label
from scipy.misc import imread,imresize,imsave
from sklearn.cluster import KMeans
import pickle
import os
from skimage.measure import regionprops
from skimage.transform import resize
from sklearn.neighbors import KNeighborsClassifier

#Same method as before...
class Extract_Letters:
	def extractFile(self, filename):
		image = imread(filename,1)
		#apply threshold in order to make the image binary
		bw = image < 120

		# remove artifacts connected to image border
		cleared = bw.copy()
		clear_border(cleared)

		# label image regions
		label_image = label(cleared,neighbors=8)
		borders = np.logical_xor(bw, cleared)
		label_image[borders] = -1

		print label_image.max()

		fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(6, 6))
		ax.imshow(bw, cmap='jet')

		#Setting Up variables
		letters = list()
		order = list()
		#if the area of the object/letter is less than 255 remove it from the array
		invalidAreaObjects = 255
		#store a list of all merged rectangle regions
		mergedRectangles = np.array([])
		#array to store non_duplicate rectangles
		uniqueArray = np.array([])
		#array which stores all non letters (e.g. scribbles on page)
		nonElements = np.array([])
		#declaring the distance between each bbox (cannot be any bigger or all letters rectangles(bbox) would merge)
		bbox_xBoundary = 40
		bbox_yBoundary = 140


		#Loop which finds all rectangles for a given image and appends them to an array
		for region in regionprops(label_image):
			minr, minc, maxr, maxc = region.bbox
			# skip small images
			if region.area > 40:
				# draw rectangle around segmented objects
				selectedRectangle = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
										  fill=False, edgecolor='red', linewidth=2)
				# add new rectangle to array
				mergedRectangles = np.append(mergedRectangles, selectedRectangle)


		# This is where all the logic happens when it comes to merging overalpping/close rectangles around a letter
		for i in range(0,mergedRectangles.size):
			#Select a rectangle from the array to compare
			selectedRectangle = mergedRectangles[i]
			for j in range(0, mergedRectangles.size):
				# go through every other rectangle and run logic gate checks
				previousRectangle = mergedRectangles[j]
				# Check to see whether the two rectangles overalap
				overlap=(selectedRectangle.get_bbox()).fully_overlaps(previousRectangle.get_bbox())or(selectedRectangle.get_bbox().x1-previousRectangle.get_bbox().x1<bbox_xBoundary and selectedRectangle.get_bbox().x1-previousRectangle.get_bbox().x1>-bbox_xBoundary)and(previousRectangle.get_bbox().y0<selectedRectangle.get_bbox().y0<previousRectangle.get_bbox().y1<selectedRectangle.get_bbox().y1)
				# The next two checks are to see whether the rectangles are within a certain distance of eachother i.e. less than the boundaries.
				checkOne=(selectedRectangle.get_bbox().y0-previousRectangle.get_bbox().y0<bbox_yBoundary and selectedRectangle.get_bbox().y0-previousRectangle.get_bbox().y0>-bbox_yBoundary)and(selectedRectangle.get_bbox().x0-previousRectangle.get_bbox().x0<bbox_xBoundary and selectedRectangle.get_bbox().x0-previousRectangle.get_bbox().x0>-bbox_xBoundary)or(selectedRectangle.get_bbox().y1-previousRectangle.get_bbox().y1<bbox_yBoundary and selectedRectangle.get_bbox().y1-previousRectangle.get_bbox().y1>-bbox_yBoundary)and(selectedRectangle.get_bbox().x1-previousRectangle.get_bbox().x1<bbox_xBoundary and selectedRectangle.get_bbox().x1-previousRectangle.get_bbox().x1>-bbox_xBoundary)
				checkTwo=(selectedRectangle.get_bbox().y0-previousRectangle.get_bbox().y1<bbox_yBoundary and selectedRectangle.get_bbox().y0-previousRectangle.get_bbox().y1>-bbox_yBoundary)and(selectedRectangle.get_bbox().x0-previousRectangle.get_bbox().x1<bbox_xBoundary and selectedRectangle.get_bbox().x0-previousRectangle.get_bbox().x1>-bbox_xBoundary)or(selectedRectangle.get_bbox().y1-previousRectangle.get_bbox().y0<bbox_yBoundary and selectedRectangle.get_bbox().y1-previousRectangle.get_bbox().y0>-bbox_yBoundary)and(selectedRectangle.get_bbox().x1-previousRectangle.get_bbox().x0<bbox_xBoundary and selectedRectangle.get_bbox().x1-previousRectangle.get_bbox().x0>-bbox_xBoundary)
				#If statement to  check logic gates
				if overlap or checkOne or checkTwo:
					print"Merging... May take a while",
					if previousRectangle.get_bbox().x0>selectedRectangle.get_bbox().x0:minc=selectedRectangle.get_bbox().x0
					else:minc=previousRectangle.get_bbox().x0
					if previousRectangle.get_bbox().x1>selectedRectangle.get_bbox().x1:maxc=previousRectangle.get_bbox().x1
					else:maxc=selectedRectangle.get_bbox().x1
					if previousRectangle.get_bbox().y0>selectedRectangle.get_bbox().y0:minr=selectedRectangle.get_bbox().y0
					else:minr=previousRectangle.get_bbox().y0
					if previousRectangle.get_bbox().y1>selectedRectangle.get_bbox().y1:maxr=previousRectangle.get_bbox().y1
					else:maxr=selectedRectangle.get_bbox().y1
					#create and store a new rectangle which consists of both previous rectangles
					newRectangle=mpatches.Rectangle((minc,minr),maxc-minc,maxr-minr,fill=False,edgecolor='red',linewidth=2)
					# store new rectangle
					mergedRectangles[j] = newRectangle
		print "Finished Merging removing non-letters"

		# This checks for objects whose areas are smaller than a given amount
		for i in range(0,mergedRectangles.size):
			#if the object is smaller than the given area store it in a new array
			if mergedRectangles[i].get_width() * mergedRectangles[i].get_height() < invalidAreaObjects: nonElements = np.append(nonElements,mergedRectangles[i])

		# This line removes all the nonElements from the main array
		mergedRectangles = np.setdiff1d(mergedRectangles,nonElements)

		print "Finished Merging removing duplicates"
		# Storing only unique rectangles in a new array (removing duplicates)
		for i in range(0,mergedRectangles.size):#check if value is unqiue or not
			noDuplicate=False
			for j in reversed(range(0,i)):#If the two rectangles are equal move onto the next one
				currentRectangle=mergedRectangles[j].get_bbox()
				comparisonRect=mergedRectangles[i].get_bbox()
				if str(currentRectangle)==str(comparisonRect):noDuplicate=True
				break
			if noDuplicate==False:uniqueArray=np.append(uniqueArray,mergedRectangles[i])

		# Going through the sorted array and adding the rectangles to the image (Checking system)
		for i in range(0,uniqueArray.size):
			ax.add_patch(uniqueArray[i])
			# getting the bbox of that rectangle and storing it in the list order for chracter extraction
			bbox = long(uniqueArray[i].get_bbox().y0), long(uniqueArray[i].get_bbox().x0), long(uniqueArray[i].get_bbox().y1), long(uniqueArray[i].get_bbox().x1)
			order.append(bbox)


		lines = list()
		first_in_line = ''
		counter = 0


		# I need to sort by y value as the bboxs are scattered randomly within the array for example (800,1500,700)
		# This will not function correctly when using your extract letters code.
		# By ordering the values correcly i can simply import your code to extract the letters
		order.sort(key=lambda tup: tup[0])
		#worst case scenario there can be 1 character per line
		for x in range(len(order)):
			lines.append([])

		for character in order:
			if first_in_line == '':
				first_in_line = character
				lines[counter].append(character)
			elif abs(character[0] - first_in_line[0]) < (first_in_line[2] - first_in_line[0]):
				lines[counter].append(character)
			elif abs(character[0] - first_in_line[0]) > (first_in_line[2] - first_in_line[0]):
				first_in_line = character
				counter += 1
				lines[counter].append(character)


		for x in range(len(lines)):
			lines[x].sort(key=lambda tup: tup[1])

		final = list()
		prev_tr = 0
		prev_line_br = 0

		for i in range(len(lines)):
			for j in range(len(lines[i])):
				tl_2 = lines[i][j][1]
				bl_2 = lines[i][j][0]
				if tl_2 > prev_tr and bl_2 > prev_line_br:
					tl,tr,bl,br = lines[i][j]
					letter_raw = bw[tl:bl,tr:br]
					letter_norm = resize(letter_raw ,(20 ,20))
					final.append(letter_norm)
					prev_tr = lines[i][j][3]
				if j == (len(lines[i])-1):

					prev_line_br = lines[i][j][2]
			prev_tr = 0
			tl_2 = 0
		print 'Characters recognized: ' + str(len(final))
		return final


		def __init__(self):
			print "Extracting characters..."

class knn_trainer:
	def train_knn_classifier(self):
		k=10
		knn_classifier = KNeighborsClassifier(n_neighbors=k)
		print knnData.shape
		knn_classifier.fit(knnData, imageLabels)
		print 'Trained the knn-classifier'
		return knn_classifier


folder_string = 'abcdefghijklmnopqrstuvwxyz123456789'
print 'folderstring -> 1: ' + str(len(folder_string))
knnData = []
imageLabels = []
string_counter = 0


#Same loop as before with a few minor changes
while string_counter < 35:
	#get path of current character
	path = './training_type/' + str(folder_string[string_counter]) + '/'
	print 'Number of training images -> 1: ' + str((path))
	filenames = sorted([filename for filename in os.listdir(path) if (filename.endswith('.jpg') or filename.endswith('.png') or (filename.endswith('.bmp'))) ])
	filenames = [path+filename for filename in filenames]
	for filename in filenames:
		#read the images
		image = imread(filename,1)
		#flatten it
		image = imresize(image, (200,200))
		#Reszing the image to a 1 dimensional array
		imageRavel = image.ravel()
		#append 1d array
		knnData.append(imageRavel)
		#add corresponding label to other array
		imageLabels.append(str(folder_string[string_counter]))
	string_counter += 1
# Store knnData as a numpy array
knnData = np.asarray(knnData)
# Store label as a numpy array
imageLabels = np.asarray(imageLabels)

# Similar to SVM but training KNN instead
knn_trainer = knn_trainer()
knnclf = knn_trainer.train_knn_classifier()

extract = Extract_Letters()
letters = extract.extractFile('./ocr/testing/testing2.jpg')
letter_count = 0

for i in letters:
	imsave('./data/' + str(letter_count) + '_snippet.png', i)
	letter_count += 1

folder_string = 'abcdefghijklmnopqrstuvwxyz123456789'

letter_count = 0
for j in letters:
	try:
		image = imread('./data/' + str(letter_count) + '_snippet.png',1) # you can modify which image is tested by changing the filename here
		image = imresize(image, (200,200))

		# conver to 1 d array
		testingLetter = image.ravel()
		# reshape to make it a 2 dimensional array
		testingLetter = testingLetter.reshape(1,-1)
		# conver to numpy array
		testingLetter = np.asarray(testingLetter)
		# get the knn value from that array for the given letter
		knn_results = knnclf.predict_proba(testingLetter)[0]
		prev_value = 0
		prev_index = 0
		# calls the classifier to predict the probability of what letter it is
		for k,result in enumerate(knn_results):
			if result > prev_value:
				prev_index = k
				prev_value = result # actual probability it is k

		#determine what letter it is in the string
		print folder_string[prev_index],
		letter_count += 1
	except Exception,e:
		print "Caught an Exception with details: %s" % e

plt.show()
