# Anime-picture-google-auto-search
使用Google自动对二次元图片以图搜图，下载到本地

## 使用方法
1. 下载项目到本地
2. 安装依赖库
```
pip install -r requirements.txt
```
3. 配置好`selenium`的浏览器驱动
```
https://learn.microsoft.com/en-us/microsoft-edge/webdriver-chromium/?tabs=c-sharp#download-microsoft-edge-webdriver
```
4. 修改`mainly.py`文件中的`folders`为你的某四个文件夹
5. 运行`mainly.py`文件
```
python mainly.py
```
6. 程序会自动搜索并下载图片到文件夹中

## 已知问题：
1. gelbooru有概率保存后回到google页面时弹出广告
2. 在保存danbooru、gelbooru的图片时有获取pixiv ID并为图片改名的功能，但部分图片可能已被删除，可以取消注释来使用，可能出现名字重复导致图片被覆盖的问题

## 未实现功能：
1. danbooru与yande.re的图片子投稿，父投稿的完全下载保存
2. 因为没有找到合适的上传图片方法，所以使用`pyautogui`模拟键盘操作，使用时会将图片路径粘贴复制到剪贴板，所以使用中不能切换别的窗口.
