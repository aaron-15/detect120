from __future__ import print_function
##CUSP UO 2016
__author__ = "fbb"

import glob
import numpy as np
import optparse
import pylab as pl
import sys
import os
import pickle as pkl
import json
import scipy.optimize
import datetime

from images2gif import writeGif
from PIL import Image, ImageSequence
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import IPython.display as IPdisplay
from statistics import mode
from scipy.stats import mode
from findImageSize import findsize
from gen_cmap import hyss_gen_cmap

OUTPUTDIR = "../outputs/"
s = json.load( open("fbb_matplotlibrc.json") )
pl.rcParams.update(s)
'''
def fixit (a,b):
    if (a-b)>1:
        if a>0 and a<=0.5:
            #then b<-1
            


    if (a-b)<-1:
'''

def myround(x):
    if np.isnan(x):
        return x
    return int(x*10+0.5)*1.0/10
     
font = {'size'   : 13}

kelly_colors_hex = [
    '#FFB300', # Vivid Yellow
    '#803E75', # Strong Purple
    '#FF6800', # Vivid Orange
    '#A6BDD7', # Very Light Blue
    '#C10020', # Vivid Red
    '#CEA262', # Grayish Yellow
    '#817066', # Medium Gray
    '#007D34', # Vivid Green
    '#F6768E', # Strong Purplish Pink
    '#00538A', # Strong Blue
    '#FF7A5C', # Strong Yellowish Pink
    '#53377A', # Strong Violet
    '#FF8E00', # Vivid Orange Yellow
    '#B32851', # Strong Purplish Red
    '#F4C800', # Vivid Greenish Yellow
    '#7F180D', # Strong Reddish Brown
    '#93AA00', # Vivid Yellowish Green
    '#593315', # Deep Yellowish Brown
    '#F13A13', # Vivid Reddish Orange
    '#232C16', # Dark Olive Green
    ]

TWODPLOT = True
#TWODPLOT = False
SINGLEPLOT = True
SINGLEPLOT = False
PLOTSTACK = True
#PLOTSTACK  = False
MXPLOT = True
#MXPLOT = False
import pandas as pd

if __name__ == '__main__':
    
    parser = optparse.OptionParser(usage="makemoneyplot.py 'filepattern' ",   
                                       conflict_handler="resolve")
    parser.add_option('--nmax', default=100, type="int",
                      help='number of images to process (i.e. timestamps)')
    parser.add_option('--lmax', default=None, type="int",
                      help='number of lights')
    
    parser.add_option('--skipfiles', default=150, type="int",
                      help="number of files to skip at the beginning")      
    parser.add_option('--coordfile', default=None, type="str",
                      help='coordinates python array (generated by windowFinder.py)')
    parser.add_option('--families', default=None, type="str",
                      help='building families file (from lassoselect.py)')
    
    parser.add_option('--fft', default=False, action="store_true",
                      help='custer in fourier space')
    parser.add_option('--onerun', default=None, type="str",
                      help='multiple bursts for a run: pass N????W????')    
    parser.add_option('--ref', default=None, type="str",
                      help='reference star (format: x,y)')
    parser.add_option('--offset', default=False, action="store_true",
                      help='plot offset thather than phase')

    
    options,  args = parser.parse_args()
    if len(args) < 1:
        sys.argv.append('--help')
        options,  args = parser.parse_args()
           
        sys.exit(0)
    
    xmax = 0
    phaseflist = []
    ref = [np.nan,np.nan]
    if options.ref:
        ref = (int(float(options.ref.split(',')[0])), int(float(options.ref.split(',')[1])))   #if 2117.12,502.52
        if options.coordfile:
            stack = np.load(options.coordfile.replace("_coords.npy",".npy"))
            imsize  = findsize(stack,
                           filepattern=options.coordfile.replace('.npy','.txt'))
            if PLOTSTACK:
                stackfig = pl.figure()
                axstack2 = stackfig.add_subplot(111)
                axstack2.imshow(stack,  interpolation='nearest')
                axstack2.set_xlim(0, axstack2.get_xlim()[1])
                axstack2.set_ylim(axstack2.get_ylim()[0], 0)
                axstack2.axis('off')
                circle1 = pl.Circle(ref, 30, color='r', fill=False, lw=2)
                axstack2.add_artist(circle1)
            
                stackfig.savefig("reflight_stack.pdf")

            fig = pl.figure(figsize=(20,10))
            axstack = fig.add_subplot(224)
            axstack.imshow(stack,  interpolation='nearest')
            axstack.set_xlim(0, axstack.get_xlim()[1])
            axstack.set_ylim(axstack.get_ylim()[0], 0)
            axstack.axis('off')
            circle1 = pl.Circle(ref, 30, color='r', fill=False, lw=2)
            axstack.add_artist(circle1)

            
        else:
            print ("missing coord file")
            sys.exit()
    else:
        fig = pl.figure(figsize=(20,10))

    fams = {}
    families = np.load(options.families)
    for i,f in enumerate(families):
        for m in f:
            fams[(int(m[0]),int(m[1]))] = i+1



    
    for arg in args:
        filepattern = arg
        #impath = os.getenv("UIdata") + filepattern
        #print ("\n\nUsing image path: %s\n\n"%impath)

        #fnameroot = filepattern.split('/')[-1]

        #flist = sorted(glob.glob(impath+"*.raw"))

        #print ("Total number of image files: %d"%len(flist))

        nmax = options.nmax
        #nmax = min(options.nmax, len(flist)-options.skipfiles)
        print ("Number of timestamps (files): %d"%(nmax))
        lmax = options.lmax
        if not lmax:
            if options.coordfile:
                print ("Using coordinates file", options.coordfile)
                try:
                    allights = np.load(options.coordfile)
                    lmax = len(allights)
                except:
                    print ("you need to create the window mask, you can use windowFinder.py")
                    sys.exit()
            elif os.path.isfile(OUTPUTDIR+filepattern+"_allights.npy") :
                try:
                    allights = np.load(OUTPUTDIR+filepattern+"_allights.npy")
                    lmax = len(allights)                    
                except:
                    print ("you need to create the window mask, you can use windowFinder.py")
                    print (OUTPUTDIR+filepattern+"_allights.npy")
                    sys.exit()

            else:
                print ("you need to create the window mask, or pass the number of windows lmax")
                sys.exit()
        
        
            if options.lmax: lmax = min([lmax, options.lmax])

    
        if not options.onerun:
            if options.fft:
                phasefilename = OUTPUTDIR+filepattern+\
                            "_fft_phases_N%04dW%04dS%04d.dat"%(nmax,
                                                               lmax,
                                                               options.skipfiles)
            else:
                phasefilename = OUTPUTDIR+filepattern+\
                            "_phases_N%04dW%04dS%04d.dat"%(nmax,
                                                           lmax,
                                                          options.skipfiles)
            phaseflist.append(phasefilename)
        else:
            print (OUTPUTDIR+filepattern+\
                            "_phases_*"+options.onerun+"S????.dat")
            
            phaseflist = np.array( glob.glob(OUTPUTDIR+filepattern+\
                            "_phases_*"+options.onerun+"S????.dat"))

    phaseflist = np.array(phaseflist)
            
    print (phaseflist)

    fft = ['','fft']
    indx = np.array(['fft' in fl for fl in phaseflist])
    print (indx)
    #(glob.glob("ESB*[0-9]_phases_N2009.dat"))
    flist1 = phaseflist[~indx]
    flist2 = phaseflist[indx]
    print (flist1)
    print (['%s'%tm for tm in np.arange(len(flist1))*15])

    
    for fi,fl in enumerate([flist1]):#,flist2]):
        #print (fl)
        ax = fig.add_subplot(2,2,fi+1)
        if SINGLEPLOT:
            fig2 = pl.figure(figsize=(10,5))            
            axref = fig2.add_subplot(111)
        else: axref = fig.add_subplot(2,2,fi+3)
        phases = []
        for f in fl:
            print ("here", f)
            try:
                phases.append(pd.read_csv(f))
                #print (phases[-1], len(phases[-1]))
                #raw_input()
            except ValueError: pass
        #print (phases)

        allcoords = []
        #np.concatenate([(p['x'].values,p['y'].values) for p in phases])

        #now i have the coordinates
        for p in phases:
            for dp in np.arange(len(p['y'].values)):
                if not ( p['x'].values[dp], p['y'].values[dp]) in allcoords:
                    allcoords.append(( p['x'].values[dp], p['y'].values[dp]))
                    #print (allcoords)
        alllights = {}
        
        for i,xy in enumerate(allcoords):
            alllights[i] = {}
            alllights[i]['xy'] = (int(xy[0]),int(xy[1]))
            
            alllights[i]['phases'] = np.zeros(len(phases))*np.nan
            alllights[i]['loc'] = np.zeros(len(phases))*np.nan
            alllights[i]['color'] = [fams[alllights[i]['xy']] if alllights[i]['xy'] in fams else 0]
            
            for j,p in enumerate(phases):
                if len(p)>0:
                    tmpind = (p.x.values.astype('int')==alllights[i]['xy'][0] )*(p.y.values.astype('int')==alllights[i]['xy'][1])
                    ph = p[tmpind].phase.values
                    if len(ph)>0:
                        alllights[i]['phases'][j]=ph - 1
                    #r = alllights[i]['xy'][0]**2+alllights[i]['xy'][1]**2
                    #if len(ph)>0 and not np.isnan(r):
                    #    alllights[i]['loc']=np.sqrt(r)
                        
        building = np.array([alllights[allg]['color'][0] for allg in alllights])
        buildingsort = np.argsort(building)[::-1]
        print (set(building))
        #allds = np.array([alllights[i]['loc'] for i in alllights])
        #allds = (allds -  allds.min())
        #allds = allds/allds.max()
        #print (allds, allds.min(), allds.max())
        for i in alllights:
            #print (ref)
            #print (alllights[i]['xy'])
            if not np.isnan(ref[0]) and alllights[i]['xy']==ref:
                isave = i
                #print (alllights[i])
                
                refphases = np.array([myround(p) for p in alllights[i]['phases']])
                if fi>0:
                    if refphases[fi]-refphases[fi-1]>1: refphases[fi]=2.0-refphases[fi]
                    if refphases[fi]-refphases[i-1]<-1: refphases[fi]=2.0+refphases[fi]
                    #if refphases[-1]-refphases[-2]<0: refphases[-1]=2.0+refphases[-1]
        print ("Ref phases",refphases)
        if np.isnan(refphases).any():
            print ("try another reference")
            sys.exit()
        #print (alllights)
        #indlist = np.arange(len(alllights)*1.0)/len(alllights)
        #np.random.shuffle(indlist)
        #maxdistance = np.nanmax([alllights[i]['loc'] for i in alllights])
        #alllights[i]['loc']/alllights[i]['loc'].max()
        #print (indlist, ph)
        #print (indlist)
        building = building.astype(float)/building.max().squeeze()
        mymap = hyss_gen_cmap()
        mycm = mymap(building[::-1])
        '''
        print (building.shape)

        print (len(mycm))
        print (mycm.max())


        #print (pl.cm.viridis(np.array((building))))

        #print( mycm)

        pl.figure()
        pl.scatter(building,building,  c=mycm)
        pl.show()
        '''
        phasediff = np.zeros((len(phases),len(alllights)))

        mymode = np.zeros(len(phases))
        myref = np.zeros(len(phases))
        if options.offset:

            for i in np.arange(len(phases)):
                
                for l in alllights:
                    phasediff[i][l]  = alllights[l]['phases'][0]-\
                                       alllights[l]['phases'][i]
                    #if phasediff[i][l]<0:
                        #print (phasediff[i][l]),
                        #phasediff[i][l] = 2.0+phasediff[i][l]
                        #print (phasediff[i][l])
                    #if phasediff[i][l]>1: phasediff[i][l]=2.0-phasediff[i][l]
                    #ax.plot(i, phasediff[l], 'o', color = mycm[l])

                    mymode[i] =  mode(phasediff[i]).mode[0]
                    #max(set(phasediff[i]), key=phasediff[i].count)
                    #np.nanmedian(phasediff[i])
                
                if not np.isnan(ref[0]):
                    #myref[i] = refphases[0] - refphases[i]
                    myref[i] = refphases[i]
                ax.scatter([i]*len(phasediff[i]), phasediff[i]-mymode[i], 
                            color = mycm, alpha=0.8, s=16)
                axref.scatter([i]*len(phasediff[i]), phasediff[i]-myref[i], 
                              color = mycm, alpha=0.8, s=16)
                #print (mymc)
                for l in alllights:
                    #phasediff[l] = alllights[l]['phases'][0]-alllights[l]['phases'][i]
                    if i>0:
                        
                        if np.abs(phasediff[i-1][l]-mymode[i-1] -
                                  phasediff[i][l]+mymode[i])<0.1:
                            #print (i, phasediff_old)
                            ax.plot([i-1,i], [phasediff[i-1][l]-mymode[i-1],
                                              phasediff[i][l]-mymode[i]],
                                    'k-', alpha=0.5)
                        else:
                        
                             ax.plot([i-1,i], [phasediff[i-1][l]-mymode[i-1],
                                              phasediff[i][l]-mymode[i]],
                                    '-', color = mycm[l], alpha=1)
                                    #'IndianRed', alpha=0.5)
                            #phasediff_old[l] = phasediff[l]

                            #axref.plot(i, phasediff[i][l]-myref[i], 'o', color = mycm[l],alpha=0.5)
                    #ax.scatter([i]*len(phasediff[i]), phasediff[i]-mymode[i], 
                    #        color = mycm, alpha=0.5)
                            
                        
                        if np.abs(phasediff[i-1][l]-myref[i-1] -
                                  phasediff[i][l]+myref[i])<0.1:
                            #print (i, phasediff_old)
                            axref.plot([i-1,i], [phasediff[i-1][l]-myref[i-1],
                                                 phasediff[i][l]-myref[i]],
                                       'k-', alpha=0.)
                        else:
                        
                            axref.plot([i-1,i], [phasediff[i-1][l]-myref[i-1],
                                                 phasediff[i][l]-myref[i]],
                                       '-', color = mycm[l], alpha=0.1)
                                       #'IndianRed', alpha=0.5)
                            #phasediff_old[l] = phasediff[l]


        else:
            mymode = np.zeros(len(phases))
            myref = np.zeros(len(phases))
            for i in np.arange(len(phases)):
                
                for l in alllights:
                    phasediff[i][l]  = myround(alllights[l]['phases'][i])
                    if not np.isnan(ref[0]):
                        #myref[i] = refphases[i]-refphases[0]
                        myref[i] = refphases[i]

                    if i>0:
                        
                        if (phasediff[i][l]-myref[i]-(phasediff[i-1][l]-myref[i-1]))>=1:
                            #print ("here1", phasediff[i][l], phasediff[i-1][l],
                            #       phasediff[i][l]- phasediff[i-1][l])
                            phasediff[i][l]-=2.0
                            #print ("\t",phasediff[i][l],
                            #       phasediff[i][l]-(phasediff[i-1][l]))
                        elif (phasediff[i][l]-myref[i]-(phasediff[i-1][l]-myref[i-1]))<=-1:
                            #print ("here2", phasediff[i][l], phasediff[i-1][l],
                            #       phasediff[i][l]- phasediff[i-1][l])
                            phasediff[i][l]=2.0+phasediff[i][l]
                            #print ("\t",phasediff[i][l],
                            #       phasediff[i][l]- (phasediff[i-1][l]))
                        #else:
                         #   continue
                    #else: continue
                    
                    mymode[i] =  mode(phasediff[i]).mode[0]

                    #max(set(phasediff[i]), key=phasediff[i].count)
                    #np.nanmedian(phasediff[i])
                


                    #print (myref)
                np.random.seed(666)
                offsetsx = np.random.randn(len(phasediff[i]))*0.04
                offsets = np.random.randn(len(phasediff[i]))*0.01
                offsets[isave]=0
                offsetsx[isave]=0
                if not TWODPLOT: continue
                
                for l in alllights:
                    #phasediff[l]  = alllights[l]['phases'][0]-alllights[l]['phases'][i]
                    #ax.scatter(i, phasediff[i][l]-mymode[i], 
                    #        color = mycm[l], alpha=0.5)
                    #if not alllights[l]['xy'] == ref:
                    #    continue
                    #print (alllights[l]['xy'])
                    if i>0:
                        
                        if np.abs(phasediff[i-1][l]-mymode[i-1] -\
                                  phasediff[i][l]+mymode[i])<0.3:
                            #print (i, phasediff_old)
                            ax.plot([i-1,i]+offsetsx[l],
                                    [(phasediff[i-1][l]-mymode[i-1]) + offsets[l],
                                     (phasediff[i][l]-mymode[i]) + offsets[l]],
                                    'k-', alpha=0.5, lw=1)
                        else:
                            ax.plot([i-1,i]+offsetsx[l],
                                    [(phasediff[i-1][l]-mymode[i-1]) + offsets[l],
                                     (phasediff[i][l]-mymode[i]) + offsets[l]],
                                    '-', color = mycm[l], alpha=0.8, lw=2)
                            #phasediff_old[l] = phasediff[l]

                        if np.abs(phasediff[i-1][l]-myref[i-1] - \
                                  phasediff[i][l]+myref[i])<0.3:
                            #print (i, phasediff_old)
                            axref.plot([i-1,i]+offsetsx[l],
                                       [(phasediff[i-1][l]-myref[i-1]) + offsets[l],
                                       (phasediff[i][l]-myref[i]) + offsets[l]],
                                       'k-', alpha=0.5, lw=1)
                        else:
                            axref.plot([i-1,i]+offsetsx[l],
                                       [(phasediff[i-1][l]-myref[i-1]) + offsets[l],
                                       (phasediff[i][l]-myref[i]) + offsets[l]],
                                       '-', color = mycm[l], alpha=0.8, lw=2)
                            #phasediff_old[l] = phasediff[l]
                if i>0:
                        
                    
                    axref.plot([i-1,i],
                            [(refphases[i-1]-myref[i-1]) ,
                             (refphases[i]-myref[i]) ],
                            'r-', alpha=0.5, lw=1)
                    
                            #phasediff_old[l] = phasediff[l]
                            
    if not options.offset and TWODPLOT:
        for fi,fl in enumerate([flist1]):
            for i in np.arange(len(phases)):                             
                ax.scatter([i]*len(phasediff[i])+offsetsx,
                           (phasediff[i]-mymode[i]) + offsets,
                            color = mycm, alpha=0.8, s=16, edgecolor='k')

                axref.scatter([i]*len(phasediff[i])+offsetsx,
                              (phasediff[i]-myref[i]) + offsets,
                              color = mycm, alpha=0.8, s=16, edgecolor='k')
        for i in np.arange(len(phases)):
            axref.scatter(i,
                          (refphases[i]-myref[i]),
                          color='r',  s=16, alpha=0.8, edgecolor='k')
                   
        right = .85
        top = .85
        bottom = .15
  
        xmax = max(xmax, ax.get_xlim()[1])
        ax.text(right, top, "using mode",
                horizontalalignment='right',
                verticalalignment='top',
                transform=ax.transAxes)

       
        ax.set_ylabel("relative phase %s "%(fft[fi]), fontsize=13)
        

        #axref.text(right, bottom, "using reference",
        #           horizontalalignment='right',
        #           verticalalignment='top',
        #           transform=axref.transAxes)
        axref.set_xlim(-0.1,xmax)
        ax.set_ylim(-1.4,1.9)
        axref.set_ylim(-1.4,1.9)        
       
        axref.set_ylabel("relative phase %s "%(fft[fi]), fontsize=15)
        if not options.onerun:
            ax.set_xlabel("time (minutes after first run)", fontsize=15)
            ax.set_xticks(range(len(flist1)))
            ax.set_xticklabels(['%s'%tm for tm in np.arange(len(flist1))*15])
            ax.set_yticklabels([r'%s$\pi$'%tm for tm in ax.get_yticks()])
            axref.set_yticklabels([r'%s$\pi$'%tm for tm in ax.get_yticks()], fontsize=15)
            axref.set_xlabel("time (minutes after first run of $CS_1$)", fontsize=15)
            axref.set_xticks(range(len(flist1)))
            axref.set_xticklabels(['%d'%tm for tm in np.arange(len(flist1))*15], fontsize=15)
        else:
            ax.set_xlabel(r"time (seconds after first burst $\mathrm{Run}_{1440}$)", fontsize=15)
            ax.set_xticks(range(len(flist1)))
            ax.set_xticklabels(['%.1f'%tm for tm in np.arange(len(flist1))*37.5])
            axref.set_xlabel(r"time (seconds after first burst $\mathrm{Run}_{1440}$)", fontsize=15)
            axref.set_xticks(range(len(flist1)))
            axref.set_xticklabels(['%.1f'%tm for tm in np.arange(len(flist1))*37.5])
            ax.set_yticklabels([r'%s$\pi$'%tm for tm in ax.get_yticks()])
            axref.set_yticklabels([r'%s$\pi$'%tm for tm in ax.get_yticks()], fontsize=15)            
        ax.set_xlim(-0.2,len(flist1)-0.8)
        axref.set_xlim(-0.2,len(flist1)-0.8)     
#        pl.xticks(range(len(flist1)),['%s'%tm for tm in np.arange(len(flist1))*15])
    if not options.onerun:
        axref.errorbar(0.1,-1.0,yerr=0.14,c='k',capsize=4,capthick=2, lw=1)
    #pl.show()
    if TWODPLOT:
        if not options.onerun:
            if options.offset:
                fig.savefig(OUTPUTDIR+"/phasesRef_phases_offset_%d_%d.pdf"%(ref[0],ref[1]))
            else:
                fig.savefig(OUTPUTDIR+"/phasesRef_phases_%d_%d.pdf"%(ref[0],ref[1]))
        else:
            if options.offset:
                fig.savefig(OUTPUTDIR+"/phasesRef_offset_%s_%d_%d.pdf"%(options.onerun,
                                                        ref[0], ref[1]))
            else:
                fig.savefig(OUTPUTDIR+"/phasesRef_phases_%s_%d_%d.pdf"%(options.onerun,
                                                        ref[0], ref[1]))
    if SINGLEPLOT:
        fig2.tight_layout()

        if not options.onerun:
            if options.offset:
                fig2.savefig(OUTPUTDIR+"phasesRef_offset_%d_%d.pdf"%(ref[0],ref[1]))
            else:
                fig2.savefig(OUTPUTDIR+"phasesRef_phases_%d_%d.pdf"%(ref[0],ref[1]))
        else:
            if options.offset:
                fig2.savefig(OUTPUTDIR+"phasesRef_offset_%s_%d_%d.pdf"%(options.onerun,
                                                        ref[0], ref[1]))
            else:
                fig2.savefig(OUTPUTDIR+"phasesRef_phases_%s_%d_%d.pdf"%(options.onerun,
                                                        ref[0], ref[1]))
    #pl.show()
    #pl.close('all')

    ax = ['']*4

    figmx, ((ax[0],ax[1]),(ax[2],ax[3])) = pl.subplots(2, 2, sharex='col', sharey='row')
    def distance(a,b):
        if np.isnan(a*b):
            return np.nan
        return np.abs(a-b)

    maxlight =(~np.isnan(phasediff[:-1,:]*phasediff[:-1,:])).sum()
    
    #if options.onerun:
    phasediffarray=[[],[],[],[],[],[]]
    if MXPLOT:
        from sklearn.preprocessing import Imputer        
        for i in np.arange(5):
            phasediffarray[i] = []
            
            #print (np.array(alllights.keys()),buildingsort)
            for a in (np.array(alllights.keys())[buildingsort]) :
                if not (np.isnan(phasediff[:,a]).sum()):
                    phasediffarray[i].append([])
                    for b in np.array(alllights.keys())[buildingsort] :
                        if not (np.isnan(phasediff[:,b]).sum()):
                            if not np.isnan(phasediff[:-1,a]*phasediff[:-1,b]).sum():
                                phasediffarray[i][-1].append(distance(phasediff[i][a],
                                                               phasediff[i][b]))
            #if np.isnan(np.array(phasediffarray[i]).sum())>0:
            #    imp = Imputer(missing_values='NaN', strategy='mean')
            #    imp.fit(phasediffarray[i])
            #    phasediffarray[i] = imp.transform(phasediffarray[i])
        
                            #phasediffarray = np.array([[distance(phasediff[i][a],
                            #                                     phasediff[i][b]) for b in alllights ] for a in alllights ])
            
            print (len(phasediffarray[i]))
        
            phasediffarray[i] = np.array(phasediffarray[i])
            phasediffarray[i][phasediffarray[i]>1] = np.abs(2.0-phasediffarray[i][phasediffarray[i]>1])
            #figlandscpe = pl.figure().add_subplot(111)

        phasediffarray = np.array(phasediffarray)

        print (phasediffarray[1].shape)
            
        for i in np.arange(4):
            print (np.isnan(phasediffarray[i+1]-phasediffarray[i]).sum())
            mx = ax[i].imshow(phasediffarray[i+1]-phasediffarray[i], 
                              interpolation='nearest', cmap='viridis',
                              vmin=0,
                              vmax=(phasediffarray[i+1]-phasediffarray[i]).max(), aspect=1,
                              extent=[0,len(phasediffarray[0]),0,len(phasediffarray[0])])
            ax[i].set_xlim(0, 33)
            ax[i].text(16,-2.4, "t = %d min"%((i+1)*15), fontsize=15, ha='center')
            ax[i].set_ylim(0, 33)
            ax[i].set_adjustable('box-forced')
            ax[i].set_xticks([])
            ax[i].set_yticks([])
            if i == 1:
                ax[i].annotate('', xy=(4.5,0), xytext=(4.5, -2),
            arrowprops=dict(facecolor='black', shrink=0.05),)
                ax[i].annotate('', xy=(0, 33-4.5), xytext=(-2, 33-4.5),
            arrowprops=dict(facecolor='black', shrink=0.05),)
            pl.grid(False)
            
            
        #except IndexError: pass
        #cbar = fig.colorbar(mx)
        figmx.subplots_adjust(right=0.8)
        cbar = figmx.add_axes([0.85, 0.15, 0.05, 0.7])
       
        cb = figmx.colorbar(mx, cax=cbar)
        cb.set_label('Change in pairwise phase difference', rotation=270,labelpad=20)
        #print (phasediffarray)
        figmx.subplots_adjust(hspace=0.1, wspace=0.05)
        #figmx.tight_layout()
        #pl.show()
        #phasediff[i][l]
        #figmx.tight_layout()
        if not options.onerun:
            if options.offset:
                figmx.savefig(OUTPUTDIR+"phasematrix_offset.pdf")
            else:
                figmx.savefig(OUTPUTDIR+"phasematrix_phases.pdf")
        else:
            if options.offset:
                figmx.savefig(OUTPUTDIR+"phasematrix_offset_%s.pdf"%(options.onerun))
            else:
                figmx.savefig(OUTPUTDIR+"phasematrix_phases_%s.pdf"%(options.onerun))
    else: pl.show()
    pl.close('all')
