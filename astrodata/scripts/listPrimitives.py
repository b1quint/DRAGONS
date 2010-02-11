#!/usr/bin/env python
import os, sys
from RECIPES_Gemini.primitives import primitives_GEMINI, primitives_GMOS_IMAGE, primitives_GMOS_OBJECT_RAW
from primitives_GEMINI import GEMINIPrimitives
from primitives_GMOS_IMAGE import GMOS_IMAGEPrimitives
from primitives_GMOS_OBJECT_RAW import GMOS_OBJECT_RAWPrimitives
from sets import Set 

# Description: 'listPrimitives' is a simple script to list available primitives both to screen and to a file
#      ( located in RECIPES_Gemini/primitives folder, primitives_List.txt ). In addition, when there are primitives  
#      with the exact same names as those in  'GEMINIPrimitives', then a list of these will be provided with a proper
#      heading at the bottom of the associated primitive list.  This allows users to quickly find out what primitives
#      override GEMINI. 
#
#      * To keep script up-to-date, one must update imports above and module_list below when adding, removing or 
#        renaming new primitive classes.
#
# Author: K.dement ( kdement@gemini.edu )
# Date: 5 Feb 2010
#
# Last Modified 9 Feb 2010 by kdement


module_list = [GEMINIPrimitives, GMOS_IMAGEPrimitives, GMOS_OBJECT_RAWPrimitives]
if os.path.isdir( '../../RECIPES_Gemini/primitives/' ):
    path =  '../../RECIPES_Gemini/primitives/primitives_List.txt'
elif os.path.isdir( '../trunk/RECIPES_Gemini' ):
    path = '../trunk/RECIPES_Gemini/primitives/primitives_List.txt'
else:
    print 'Writing out primitives_List.txt to current Directory'
    path = 'primitives_List.txt'
try:
    os.system( 'rm ' + path )
except:
    pass
fhandler = open( path , 'w' )
geminiList=[]
childList=[]
intersectionList=[]
outerloop = 0
print '_'*60
fhandler.write( '_'*60 )
for m in module_list:
    print '\n',m.__name__,'\n','-'*60,'\n'
    fhandler.write( '\n')
    fhandler.write( m.__name__ )
    fhandler.write( '\n' )
    fhandler.write( '-'*60 )
    fhandler.write( '\n' )
    if outerloop > 1:
        childList=[]
    if outerloop is 0:
        for key in m.__dict__:   
            if not key.startswith('_') and key!='init' and key!='pause':
                geminiList.append( key )
        one = Set( geminiList )        
        geminiList.sort()
        count = 1
        for mf in geminiList:
            print count, '. ', mf
            fhandler.write( str( count)  )
            fhandler.write( '. ' )
            fhandler.write( mf )
            fhandler.write( '\n' )
            count = count + 1        
    else:
        for key in m.__dict__:   
            if not key.startswith('_') and key!='init':
                childList.append( key )
        two = Set( childList )        
        childList.sort()
        count = 1
        for mf in childList:
            print count, '. ', mf
            fhandler.write( str( count)  )
            fhandler.write( '. ' )
            fhandler.write( mf )
            fhandler.write( '\n' )
            count = count + 1
        two = Set( childList )
        newSet = one & two
        if len(newSet) > 1:
            intersectionList = list( newSet )
            intersectionList.sort()
            if len( intersectionList ) != len( geminiList ):
                print '- '*30
                print 'Primitives listed here that override GEMINIPrimitives'
                print '- '*30
                fhandler.write ( '- '*30 )
                fhandler.write( '\n' )
                fhandler.write ( 'Primitives listed here that override GEMINIPrimitives' )
                fhandler.write( '\n' )
                fhandler.write ( '- '*30 )
                fhandler.write( '\n' )
                for i in intersectionList:
                    print i
                    fhandler.write( i )
                    fhandler.write( '\n' )    
    print '\n\n'   
    fhandler.write( '\n\n' )
    print '_'*60
    fhandler.write( '_'*60 )
    outerloop = outerloop + 1
print '\n\n'
fhandler.write( '\n\n' )
fhandler.close()
