"""
Code for representing each block
"""

class Block:
	color = ""
	size = "small"
	xloc = 0
	yloc = 0

	def getColor(self):
		return self.color

	def getSize(self):
		return self.size

	def getLocation(self):
		return self.xloc, self.yloc

	def setColor(self, newColor):
		self.color = newColor

	def setSize(self, newSize):
		self.size = newSize

	def setLocation(self, newx, newy):
		self.xloc = newx
		self.yloc = newy

