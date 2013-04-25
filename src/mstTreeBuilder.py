class SyntacticTreeNode:
	def __init__(self, word, label):
		self.word = word
		self.label = label
		self.children = []

	def addChild(self, child):
		self.children.append(child)

	def toString(self):
		return "("+self.label+" "+self.word+" "+";".join([t.toString() for t in self.children])+")"

def buildSyntacticTree(mstOutput):
	(wordsLine, labelsLine, parentsLine) = mstOutput.split("\n")
	words = wordsLine.split("\t")
	labels = labelsLine.split("\t")
	parents = [int(n) for n in parentsLine.split("\t")]

	return buildTreeFrom(findChildAfter(0, 1, parents), words, labels, parents)


'''
Return the position (real offset + 1) of the first children of $father
which position is greater than or equal to $minPos
'''
def findChildAfter(father, minPos, parents):
	for i in range(minPos - 1, len(parents)):
		if father == parents[i]:
			return (i+1)

	return 0

'''
Return the subtree which root is at position $root
'''
def buildTreeFrom(root, words, labels, parents):
	if root <= 0 or root > len(words):
		return None

	result = SyntacticTreeNode(words[root - 1], labels[root - 1])

	nextChildPos = findChildAfter(root, 1, parents)
	while nextChildPos != 0:
		result.addChild(buildTreeFrom(nextChildPos, words, labels, parents))
		nextChildPos = findChildAfter(root, nextChildPos + 1, parents)

	return result
