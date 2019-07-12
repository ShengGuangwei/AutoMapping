# coding=utf-8
import arcpy as ap
from arcpy.sa import *
import os
import os.path
import time


def getFileName(dirName, postfix):
    # 存储符合条件的影像路径
    imgFileList = []
    # 寻找给定文件夹下符合条件的文件，并添加到imgFileList中
    for maindir, subdir, fileList in os.walk(dirName):
        for fileName in fileList:
            imgPath = os.path.join(maindir, fileName)
            for label in postfix:
                if fileName[-len(label):] == label:
                    try:
                        imgFileList.append(imgPath)
                    except:
                        pass
    return imgFileList

def clipRaster(imgFileList, inMaskData):
    # 存储裁剪后的文件路径
    crList = []
    # 裁剪
    for imgFile in imgFileList:
        imgName = os.path.basename(imgFile)
        try:
            inRaster = imgFile
            crFile = imgFile[:-4] + "_clip" + ".tif"
            ap.CheckOutExtension("Spatial")
            outExtractByMask = ExtractByMask(inRaster, inMaskData)
        except:
            print "  -> " + imgName + " error"
        else:
            outExtractByMask.save(crFile)
            crList.append(crFile)

            print "  -> " + imgName + " done"

    return crList


print "Waiting..."
# 设置工作路径即缓存路径，对 "MapDocument"无效
ap.env.workspace = r"E:\ShengGW\SnowMapping\ThemticMap\Cache"
# 设置文件存储路径
# os.chdir(r"E:\ShengGW\SnowMapping\ThemticMap")

# 读取制图所需数据
dirname = r"E:\ShengGW\SnowMapping\AlbeodoData"
imgFileList = getFileName(dirname, {'_clip.tif'})

print "Cliping..."

# 影像裁剪
# 读取矢量边界
t1 = time.time()
inMaskData = r"E:\ShengGW\SnowMapping\ArcGIS\MAP_shp\国界_polygon.shp"
crList = clipRaster(imgFileList, inMaskData)
t2 = time.time()
print "  -> " + "cost: " + str(int(t2 - t1)) + "s"

print "Mapping..."

# 读取.mxd文档
mxd = ap.mapping.MapDocument(r"E:\ShengGW\SnowMapping\ArcGIS\SnowAlbedo.mxd")
# 读取符号系统
colorramp = ap.mapping.Layer(r"E:\ShengGW\SnowMapping\ArcGIS\colorramp2_albedo.lyr")
# 读取mxd中的数据框列表
df = ap.mapping.ListDataFrames(mxd)

for imgpath in crList:
    t3 = time.time()
    addlyr = ap.mapping.Layer(imgpath)
    addlyr2 = ap.mapping.Layer(imgpath)
    mapName = os.path.basename(imgpath)
    # 将数据图层添加到数据框1中
    ap.mapping.AddLayer(df[0], addlyr, "BOTTOM")
    lyr = ap.mapping.ListLayers(mxd, "", df[0])
    imagelyr = lyr[-1]
    # 将数据图层添加到数据框2中
    ap.mapping.AddLayer(df[1], addlyr2, "BOTTOM")
    lyr2 = ap.mapping.ListLayers(mxd, "", df[1])
    imagelyr2 = lyr2[-1]

    # 更新addlyr的符号系统
    ap.mapping.UpdateLayer(df[0], imagelyr, colorramp, True)
    ap.mapping.UpdateLayer(df[1], imagelyr2, colorramp, True)
    if addlyr.symbologyType == "RASTER_CLASSIFIED":
        addlyr.symbology.reclassify()
    if addlyr2.symbologyType == "RASTER_CLASSIFIED":
        addlyr2.symbology.reclassify()

    # 地图整饰
    elemlist = ap.mapping.ListLayoutElements(mxd)
    for elem in elemlist:
        if elem.name == "datetitle":
            elem.text = mapName[:4] + "年" + mapName[4:6] + "月"
            elem.elementPositionX = 155
            elem.elementPositionY = 475

    # 导出地图
    ap.mapping.ExportToTIFF(mxd, "E:/ShengGW/SnowMapping/ThemticMap/" + mapName[:-9] + "_albedo_map.tif")
    # 删除此数据对应的图层
    ap.mapping.RemoveLayer(df[0], lyr[-1])
    ap.mapping.RemoveLayer(df[1], lyr2[-1])

    t4 = time.time()
    print "  -> " + addlyr.name + " done" + " | " + "cost: " + str(int(t4 - t3)) + "s"

    del addlyr, addlyr2

mxd.save()