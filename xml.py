import xml.etree.ElementTree as ElementTree


def getValue(self):

	tree = ElementTree.parse('G:/settings.xml')
	root = tree.getroot()

	for elem in root:
		if elem.tag == 'Id':
			for child in elem:
				if child.attrib['name'] == 'zwei':
					print (child.text)

def setValue(self):

	tree = ElementTree.parse('G:/settings.xml')
	root = tree.getroot()

	for elem in root:
		if elem.tag == 'Id':
			for child in elem:
				if child.attrib['name'] == 'zwei':
					child.text = 'xxx'
	tree.write("G:/settings.xml")