# This recipe performs the standardization and corrections needed to convert 
# the raw input bias images into a single stacked bias image. This output 
# processed bias is stored on disk using storeProcessedBias and has a name 
# equal to the name of the first input bias image with "_bias.fits" appended.
recipe_tags = set(['GMOS', 'CAL', 'BIAS'])

def makeProcessedBias(p):
    p.prepare()
    p.addDQ()
    p.addVAR(read_noise=True)()
    p.overscanCorrect()
    p.addToList(purpose="forStack")
    p.getList(purpose="forStack")
    p.stackFrames()
    p.storeProcessedBias()
    return

default = makeProcessedBias