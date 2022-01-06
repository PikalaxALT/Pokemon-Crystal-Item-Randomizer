import os
import Location
import Gym
import yaml
from collections import defaultdict

def readTSVFile(filename):
    file = open(filename)
    data = file.readlines()

    objs = []

    first_line = True
    for line in data:
        if first_line:
            field_names = line.strip().split("\t")
            first_line = False
        else:
            d = line.strip().split("\t")
            obj = {}
            iterator = 0
            for name in field_names:
                obj[name] = d[iterator]
                iterator += 1

            objs.append(obj)

    return objs


def LoadWarpData(locationList):
	warpLocations = []

	# var
	# formattedString = String.format("%s\t(%s)\t->\t%s\t(%s)",
	# 								this.StartFriendlyName, this.StartGroupName,
	# 								this.EndFriendlyName, this.EndGroupName);

#Start Warp Name	Start Warp Group	->	End Warp Name	End Warp Group
	warpOutput = "Warp Data/warp-output.tsv"
	warpTSV = readTSVFile(warpOutput)

	accepted_warps = CheckLocationData(warpTSV, locationList)

	for data in accepted_warps:
		fromGroupName = data["Start Warp Group"][1:-1]
		toGroupName = data["End Warp Group"][1:-1]

		## TODO Unlock default test using only cherrygrove-based warps
		#if fromGroupName != "Cherrygove":
		#	continue

		locationData = {
			"Name": toGroupName+" Warpie",
			"FileName": "",
			"Type": "Map",
			"WildTableList": None,
			"LocationReqs": [fromGroupName+" Warpie"],
			"FlagReqs": None,
			"FlagsSet": None,
			"ItemReqs": None,
			"Code": "",
			"Text": "",
			"Sublocations": None,
			"HasPKMN": "No",
			"ReachableReqs": None,
			"TrainerList": None
		}

		l = Location.Location(locationData)

		warpLocations.append(l)

	# TODO: Investigate methods to remove inaccessible warp locations
	# Closed loops, etc, and mark as impossible

	return warpLocations


def ImpossibleWarpRecursion(accessible_groups, l):
	for l_s in l.Sublocations:
		ImpossibleWarpRecursion(accessible_groups,l_s)

	if l.WarpReqs is not None and len(l.WarpReqs) > 0 and l.WarpReqs[0] + " Warpie" not in accessible_groups and \
			"Impossible" not in l.FlagReqs:
		l.FlagReqs.append("Impossible")
		print("Now impossible:", l.Name)


def isValidWarpDesc(warpData):
	invalidWarps = ["x","X","null","NULL",""]

	if warpData["End Warp Name"] in invalidWarps:
		return False

	warpGroup = warpData["End Warp Group"][1:-1]
	if warpGroup in invalidWarps:
		return False

	if warpData["Start Warp Name"] in invalidWarps :
		return False

	warpGroup = warpData["Start Warp Group"][1:-1]
	if warpGroup in invalidWarps:
		return False

	return True


def CheckLocationData(warpLocations, locationList):
	# Currently ignores crossover logic
	# This is presently defined in Warp Data/WarpCrossoverData.yml
	# These should be usable as standard locations but not for marking as 'impossible'

	accessible_groups = ["New Bark Warpie","Cherrygrove Warpie"]
	accessible_warp_data = []

	flattened = FlattenLocationTree(locationList)

	while True:
		added_cycle = 0

		for warp in warpLocations:

			if not isValidWarpDesc(warp):
				continue

			start = warp["Start Warp Group"][1:-1] + " Warpie"
			end = warp["End Warp Group"][1:-1] + " Warpie"

			if start in accessible_groups:
				#print("Add warp access:",start,end)


				if end not in accessible_groups:
					accessible_groups.append(end)
					added_cycle += 1

				if warp not in accessible_warp_data:
					accessible_warp_data.append(warp)
					added_cycle += 1


			# Is not flattened!
			elif start not in accessible_groups:
				otherPossibilities = list(filter(lambda x: \
					x.Name == start, flattened))

				for op in otherPossibilities:
					for lreq in op.LocationReqs:
						if lreq in accessible_groups:
							if op.Name not in accessible_groups:
								#print("Add warp access2:", start,end)
								accessible_groups.append(start)
								accessible_groups.append(end)
								added_cycle += 2
							if warp not in accessible_warp_data:
								accessible_warp_data.append(warp)
								added_cycle += 1

		if added_cycle == 0:
			break

	for l in locationList:
		ImpossibleWarpRecursion(accessible_groups, l)




	return accessible_warp_data










def LoadDataFromFolder(path, banList = None, allowList = None, modifierDict = {}, flags = [], labelling = False):
	LocationList = []
	LocCountDict = defaultdict(lambda: 0)
	print("Creating Locations")
	for root, dir, files  in os.walk(path+"//Map Data"):
		for file in files:
			#print("File: "+file)
			entry = open(path+"//Map Data//"+file,'r',encoding='utf-8')
			try:
				yamlData = yaml.load(entry, Loader=yaml.FullLoader)
			except Exception as inst:
				raise(inst)
			#print("Locations in file are:")
			for location in yamlData["Location"]:
				#print(location["Name"])
				try:
					nLoc = Location.Location(location)
					if "Warps" in flags:
						nLoc.applyWarpLogic()
					nLoc.applyBanList(banList,allowList)
					nLoc.applyModifiers(modifierDict)
					LocationList.append(nLoc)
					LocCountDict[nLoc.Name] = LocCountDict[nLoc.Name]+1
				except Exception as inst:
					print("-----------")
					print("Failure in "+location["Name"])
					raise(inst)
	print("Creating Gyms")
	for groot, gdir, gfiles  in os.walk("Gym Data"):
		for gfile in gfiles:
			#print("File: "+gfile)
			entry = open(path+"//Gym Data//"+gfile,'r',encoding='utf-8')
			yamlData = yaml.load(entry,Loader=yaml.FullLoader)

			#print("Locations in file are:")
			for location in yamlData["Location"]:
				#print(location["Name"])
				try:
					nLoc = Gym.Gym(location)
					if "Warps" in flags:
						nLoc.applyWarpLogic()
					nLoc.applyBanList(banList,allowList)
					nLoc.applyModifiers(modifierDict)
					LocationList.append(nLoc)
				except Exception as inst:
					print("-----------")
					print("Failure in "+location["Name"])
					raise(inst)

	if "Warps" in flags:
		warpData = LoadWarpData(LocationList)
		for warp in warpData:
			LocationList.append(warp)

	trashList = []
	for i in LocationList:
		trashList.extend(i.getTrashItemList(flags, labelling))
		
	#print('NameCounts')
	#print(LocCountDict)
	return (LocationList,trashList)
	
def FlattenLocationTree(locations):
	nList = []
	aList = []
	done = False
	while not done:
		done = True
		aList = []
		for i in locations:
			nList.append(i)
			#print('Flattened :'+i.Name)
			for j in i.Sublocations:
				aList.append(j)
				done = False
		locations = aList
	return nList
		