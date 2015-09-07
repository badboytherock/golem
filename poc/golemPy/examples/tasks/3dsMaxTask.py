import os
import sys
import glob
import cPickle as pickle
import zlib
import zipfile
import subprocess
import win32process
import shutil

def format3dsMaxCmd(cmdFile, startTask, endTask, totalTasks, outputFile, outfilebasename, scenefile, width, height, presetFile, overlap):
    cmd = '{} -outputName:{}\\{}.exr -strip:{},{},{} "{}" -frames:0 -stillFrame -rfw:0 -width={} -height={} -rps:"{}"'.format(cmdFile,outputFile,  outfilebasename, totalTasks, overlap, startTask, scenefile, width, height, presetFile)
    return cmd

def format3dsMaxCmdWithFrames(cmdFile, frames, outputFile, outfilebasename, scenefile, width, height, presetFile):
    cmd = '{} -outputName:{}\\{}.exr -frames:{} "{}" -rfw:0 -width={} -height={} -rps:"{}"'.format(cmdFile, outputFile, outfilebasename, frames, scenefile, width, height, presetFile)
    return cmd

def format3dsMaxCmdWithParts(cmdFile, frames, parts, startTask, outputFile, outfilebasename, sceneFile, width, height, presetFile, overlap):
    part = ((startTask - 1) % parts) + 1
    cmd = '{} -outputName:{}\\{}.exr -frames:{} -strip:{},{},{} "{}" -rfw:0 -width={} -height={} -rps:"{}"'.format(cmdFile, outputFile, outfilebasename, frames, parts, overlap, part, sceneFile, width, height, presetFile)
    return cmd

def __readFromEnvironment(defaultCmdFile, num_cores):
    GOLEM_ENV = 'GOLEM'
    path = os.environ.get(GOLEM_ENV)
    if not path:
        print "No Golem environment variable found... Assuming that exec is in working folder"
        return defaultCmdFile

    sys.path.append(path)

    from examples.gnr.RenderingEnvironment import ThreeDSMaxEnvironment
    env = ThreeDSMaxEnvironment()
    cmdFile = env.get3dsmaxcmdPath()
    if cmdFile:
    #    env.setNThreads(num_cores)
        return cmdFile
    else:
        print "Environment not supported... Assuming that exec is in working folder"
        return defaultCmdFile

###########################
def returnData(files):
    res = []
    for f in files:
        with open(f, "rb") as fh:
            fileData = fh.read()
        fileData = zlib.compress(fileData, 9)
        res.append(pickle.dumps((os.path.basename(f), fileData)))

    return { 'data': res, 'resultType': 0 }

############################
def returnFiles(files):
    copyPath = os.path.normpath(os.path.join(tmpPath, ".."))
    for f in files:
        shutil.copy2(f, copyPath)

    files = [ os.path.normpath(os.path.join(copyPath, os.path.basename(f))) for f in files]
    return {'data': files, 'resultType': 1 }



############################f =
def run3dsMaxTask(pathRoot, startTask, endTask, totalTasks, outfilebasename, sceneFile, width, height, preset, cmdFile, useFrames, frames, parts, num_cores, overlap):
    print 'run3dsMaxTask'
    outputFiles = tmpPath

    files = glob.glob(outputFiles + "*.exr")

    for f in files:
        os.remove(f)

    if os.path.splitext(sceneFile)[1] == '.zip':
        with zipfile.ZipFile(sceneFile , "r", allowZip64 = True) as z:
            z.extractall(os.getcwd())
        sceneFile = glob.glob("*.max")[0]

    if preset:
        presetFile = os.path.normpath( os.path.join(os.getcwd(), preset))
    else:
        presetFile = os.path.join(dsmaxpath,  'renderpresets\mental.ray.daylighting.high.rps')


    cmdFile = __readFromEnvironment(cmdFile, num_cores)
    if os.path.exists(sceneFile):
        if useFrames:
            frames = parseFrames(frames)
            if parts == 1:
                cmd = format3dsMaxCmdWithFrames(cmdFile, frames, outputFiles, outfilebasename, sceneFile, width, height, presetFile)
            else:
                cmd = format3dsMaxCmdWithParts(cmdFile, frames, parts, startTask, outputFiles, outfilebasename, sceneFile, width, height, presetFile, overlap)
        else:
            cmd = format3dsMaxCmd(cmdFile, startTask, endTask, totalTasks, outputFiles, outfilebasename, sceneFile, width, height, presetFile, overlap)

    else:
        print "Scene file does not exist"
        return {'data': [], 'resultType': 0 }

    print cmd

    pc = subprocess.Popen(cmd)

    win32process.SetPriorityClass(pc._handle, win32process.IDLE_PRIORITY_CLASS)


    pc.wait()

    files = glob.glob(outputFiles + "\*.exr")

    return returnData(files)

def parseFrames(frames):
    return ",".join([ u"{}".format(frame) for frame in frames ])

output = run3dsMaxTask (pathRoot, startTask, endTask, totalTasks, outfilebasename, sceneFile, width, height, presetFile, cmdFile, useFrames, frames, parts, num_cores, overlap)
