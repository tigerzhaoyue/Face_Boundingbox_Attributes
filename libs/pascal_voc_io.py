#!/usr/bin/env python
# -*- coding: utf8 -*-
import sys
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement
from lxml import etree
import codecs

XML_EXT = '.xml'
ENCODE_METHOD = 'utf-8'

class PascalVocWriter:

    def __init__(self, foldername, filename, imgSize,databaseSrc='Unknown', localImgPath=None):
        self.foldername = foldername
        self.filename = filename
        self.databaseSrc = databaseSrc
        self.imgSize = imgSize
        self.boxlist = []
        self.localImgPath = localImgPath
        self.verified = False

    def prettify(self, elem):
        """
            Return a pretty-printed XML string for the Element.
        """
        rough_string = ElementTree.tostring(elem, 'utf8')
        root = etree.fromstring(rough_string)
        return etree.tostring(root, pretty_print=True, encoding=ENCODE_METHOD).replace("  ".encode(), "\t".encode())
        # minidom does not support UTF-8
        '''reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="\t", encoding=ENCODE_METHOD)'''

    def genXML(self):
        """
            Return XML root
        """
        # Check conditions
        if self.filename is None or \
                self.foldername is None or \
                self.imgSize is None:
            return None

        top = Element('annotation')
        if self.verified:
            top.set('verified', 'yes')

        folder = SubElement(top, 'folder')
        folder.text = self.foldername

        filename = SubElement(top, 'filename')
        filename.text = self.filename

        if self.localImgPath is not None:
            localImgPath = SubElement(top, 'path')
            localImgPath.text = self.localImgPath

        source = SubElement(top, 'source')
        database = SubElement(source, 'database')
        database.text = self.databaseSrc

        size_part = SubElement(top, 'size')
        width = SubElement(size_part, 'width')
        height = SubElement(size_part, 'height')
        depth = SubElement(size_part, 'depth')
        width.text = str(self.imgSize[1])
        height.text = str(self.imgSize[0])
        if len(self.imgSize) == 3:
            depth.text = str(self.imgSize[2])
        else:
            depth.text = '1'

        segmented = SubElement(top, 'segmented')
        segmented.text = '0'
        return top

    def addBndBox(self, xmin, ymin, xmax, ymax, name, gender, age,
                  emotion, illumination, blurriness, occlusion, yaw, roll, pitch):
        bndbox = {'xmin': xmin, 'ymin': ymin, 'xmax': xmax, 'ymax': ymax}
        bndbox['name'] = name
        bndbox['gender'] = gender
        bndbox['age'] = age
        bndbox['emotion'] = emotion
        bndbox['illumination'] = illumination
        bndbox['blurriness'] = blurriness
        bndbox['occlusion'] = occlusion
        bndbox['yaw'] = yaw
        bndbox['roll'] = roll
        bndbox['pitch'] = pitch
        self.boxlist.append(bndbox)

    def appendObjects(self, top):
        for each_object in self.boxlist:
            object_item = SubElement(top, 'object')
            name = SubElement(object_item, 'name')
            try:
                name.text = unicode(each_object['name'])
            except NameError:
                # Py3: NameError: name 'unicode' is not defined
                name.text = each_object['name']

            truncated = SubElement(object_item, 'truncated')
            if int(each_object['ymax']) == int(self.imgSize[0]) or (int(each_object['ymin'])== 1):
                truncated.text = "1" # max == height or min
            elif (int(each_object['xmax'])==int(self.imgSize[1])) or (int(each_object['xmin'])== 1):
                truncated.text = "1" # max == width or min
            else:
                truncated.text = "0"

            gender = SubElement(object_item, 'gender')
            gender.text = str(bool(each_object['gender']) & 1 )

            age = SubElement(object_item, 'age')
            age.text = str(each_object['age'])

            blurriness = SubElement(object_item, 'blurriness')
            blurriness.text = str(bool(each_object['blurriness']) & 1 )

            emotion = SubElement(object_item, 'emotion')
            emotion.text = str(each_object['emotion'])

            illumination = SubElement(object_item, 'illumination')
            illumination.text = str(each_object['illumination'])

            occlusion = SubElement(object_item, 'occlusion')
            occlusion.text = str(each_object['occlusion'])

            yaw = SubElement(object_item, 'yaw')
            yaw.text = str(each_object['yaw'])

            roll = SubElement(object_item, 'roll')
            roll.text = str(each_object['roll'])

            pitch = SubElement(object_item, 'pitch')
            pitch.text = str(each_object['pitch'])

            bndbox = SubElement(object_item, 'bndbox')
            xmin = SubElement(bndbox, 'xmin')
            xmin.text = str(each_object['xmin'])
            ymin = SubElement(bndbox, 'ymin')
            ymin.text = str(each_object['ymin'])
            xmax = SubElement(bndbox, 'xmax')
            xmax.text = str(each_object['xmax'])
            ymax = SubElement(bndbox, 'ymax')
            ymax.text = str(each_object['ymax'])

    def save(self, targetFile=None):
        root = self.genXML()
        self.appendObjects(root)
        out_file = None
        if targetFile is None:
            out_file = codecs.open(
                self.filename + XML_EXT, 'w', encoding=ENCODE_METHOD)
        else:
            out_file = codecs.open(targetFile, 'w', encoding=ENCODE_METHOD)

        prettifyResult = self.prettify(root)
        out_file.write(prettifyResult.decode('utf8'))
        out_file.close()


class PascalVocReader:

    def __init__(self, filepath):
        # shapes type:
        # [labbel, [(x1,y1), (x2,y2), (x3,y3), (x4,y4)], color, color, ismale]
        self.shapes = []
        self.filepath = filepath
        self.verified = False
        try:
            self.parseXML()
        except:
            pass

    def getShapes(self):
        return self.shapes

    def addShape(self, label, bndbox,
                 ismale, isfemale,
                 age,
                 noblur, blur,
                 norm_emotion, laugh, shock,
                 norm_illumination, dim, bright, backlight, yinyang,
                 no_occlusion, partial, heavy, sunglasses,
                 norm_yaw, yaw_30, yaw_60,
                 norm_roll, roll_20, roll_45,
                 norm_pitch, pitch_20up, pitch_45up, pitch_20down, pitch_45down):
        xmin = int(bndbox.find('xmin').text)
        ymin = int(bndbox.find('ymin').text)
        xmax = int(bndbox.find('xmax').text)
        ymax = int(bndbox.find('ymax').text)
        points = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]
        self.shapes.append((label, points, None, None,
                            ismale, isfemale,
                            age,
                            noblur, blur,
                            norm_emotion, laugh, shock,
                            norm_illumination, dim, bright, backlight, yinyang,
                            no_occlusion, partial, heavy, sunglasses,
                            norm_yaw, yaw_30, yaw_60,
                            norm_roll, roll_20, roll_45,
                            norm_pitch, pitch_20up, pitch_45up, pitch_20down, pitch_45down
                            ))

    def parseXML(self):
        assert self.filepath.endswith(XML_EXT), "Unsupport file format"
        parser = etree.XMLParser(encoding=ENCODE_METHOD)
        xmltree = ElementTree.parse(self.filepath, parser=parser).getroot()
        filename = xmltree.find('filename').text
        try:
            verified = xmltree.attrib['verified']
            if verified == 'yes':
                self.verified = True
        except KeyError:
            self.verified = False

        for object_iter in xmltree.findall('object'):
            bndbox = object_iter.find("bndbox")
            label = object_iter.find('name').text

            # Add chris
            ismale = False
            isfemale = False
            noblur = False
            blur = False
            norm_emotion = False
            laugh = False
            shock = False
            norm_illumination = False
            dim = False
            bright = False
            backlight = False
            yinyang = False
            no_occlusion = False
            partial = False
            heavy = False
            sunglasses = False
            norm_yaw = False
            yaw_30 = False
            yaw_60 = False
            norm_roll = False
            roll_20 = False
            roll_45 = False
            norm_pitch = False
            pitch_20up = False
            pitch_45up = False
            pitch_20down = False
            pitch_45down = False
            age = 0

            if object_iter.find('gender') is not None:
                ismale = bool(int(object_iter.find('gender').text))
                if ismale:
                    isfemale = False
                else:
                    isfemale = True

            if object_iter.find('blurriness') is not None:
                blur = bool(int(object_iter.find('blurriness').text))
                if blur:
                    noblur = False
                else:
                    noblur = True

            if object_iter.find('emotion') is not None:
                if int(object_iter.find('emotion').text) == 1:
                    laugh = True
                elif int(object_iter.find('emotion').text) == 2:
                    shock = True
                else:
                    norm_emotion = True

            if object_iter.find('illumination') is not None:
                if int(object_iter.find('illumination').text) == 1:
                    dim = True
                elif int(object_iter.find('illumination').text) == 2:
                    bright = True
                elif int(object_iter.find('illumination').text) == 3:
                    backlight = True
                elif int(object_iter.find('illumination').text) == 4:
                    yinyang = True
                else:
                    norm_illumination = True

            if object_iter.find('occlusion') is not None:
                if int(object_iter.find('occlusion').text) == 1:
                    partial = True
                elif int(object_iter.find('occlusion').text) == 2:
                    heavy = True
                elif int(object_iter.find('occlusion').text) == 3:
                    sunglasses = True
                else:
                    no_occlusion = True

            if object_iter.find('yaw') is not None:
                if int(object_iter.find('yaw').text) == 1:
                    yaw_30 = True
                elif int(object_iter.find('yaw').text) == 2:
                    yaw_60 = True
                else:
                    norm_yaw = True

            if object_iter.find('roll') is not None:
                if int(object_iter.find('roll').text) == 1:
                    roll_20 = True
                elif int(object_iter.find('roll').text) == 2:
                    roll_45 = True
                else:
                    norm_roll = True

            if object_iter.find('pitch') is not None:
                if int(object_iter.find('pitch').text) == 1:
                    pitch_20up = True
                elif int(object_iter.find('pitch').text) == 2:
                    pitch_45up = True
                elif int(object_iter.find('pitch').text) == 3:
                    pitch_20down = True
                elif int(object_iter.find('pitch').text) == 4:
                    pitch_45down = True
                else:
                    norm_pitch = True

            if object_iter.find('age') is not None:
                age = int(object_iter.find('age').text)
            self.addShape(label, bndbox,
                          ismale, isfemale,
                          age,
                          noblur, blur,
                          norm_emotion,laugh, shock,
                          norm_illumination, dim, bright, backlight, yinyang,
                          no_occlusion, partial, heavy, sunglasses,
                          norm_yaw, yaw_30, yaw_60,
                          norm_roll, roll_20, roll_45,
                          norm_pitch, pitch_20up, pitch_45up, pitch_20down, pitch_45down)
        return True
