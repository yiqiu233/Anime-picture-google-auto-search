from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from requests.exceptions import HTTPError
from urllib.parse import urlparse
from selenium import webdriver
import pyautogui
import pyperclip
import requests
import shutil
import urllib
import time
import glob
import os
import re

pyautogui.PAUSE = 1  # 每个 pyautogui 命令执行后暂停 1 秒
pyautogui.FAILSAFE = True  # 激活 FAILSAFE 保护机制

options = webdriver.EdgeOptions()
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0")
options.add_argument("--disable-extensions")
options.add_argument("--log-level=3")
options.add_argument("--inprivate")  # 无痕模式
options.add_argument("--ignore-certificate-errors")
options.add_experimental_option('excludeSwitches', ['enable-logging'])  # 禁用控制台日志
options.add_experimental_option('detach', True)
driver = webdriver.Edge(options=options)

def google_image_search(file_path: str, timeout: int = 15) -> bool:
    try:
        # 打开Google图片搜索页面
        driver.get("https://images.google.com")
        # 点击相机图标打开上传菜单
        camera_button = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "body > div.L3eUgb > div.o3j99.ikrT4e.om7nvf > form > div:nth-child(1) > div.A8SBwf > div.RNNXgb > div.SDkEP > div.fM33ce.dRYYxd > div.nDcEnd"))
        )
        camera_button.click()
        
        time.sleep(1)
        pyautogui.press('enter')
        pyperclip.copy(file_path)
        time.sleep(1)
        pyautogui.hotkey("ctrl", "v")
        pyautogui.press('enter')
        print(f"开始搜索 {file_path} ")
        
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#rso"))
        )
        pyautogui.scroll(-150)
        full_match_button = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,"#rso > div.ULSxyf > div > div > div > div > div > div > div:nth-child(1) > div > div > div:nth-child(2) > a > div > div:nth-child(3) > div > div:nth-child(2) > div > span.mIZQhd"))
        )
        driver.execute_script("arguments[0].click();", full_match_button)
        time.sleep(3)
        pyautogui.scroll(-150)
        return True
    except TimeoutException as e:
        print(f"操作超时: {e}")
        return False
    except Exception as e:
        print(f"搜索失败: {e}")
        return False

def image_locate(timeout: int = 10) -> dict:
    urls = {
        "danbooru": "danbooru.donmai.us/posts/",
        "gelbooru": "gelbooru.com/index.php?page=post&s=view&id=",
        "yande": "yande.re/post/show/"
    }
    # 初始化结果字典 {站点名: URL}
    links_dict = {site: None for site in urls}
    try:
        # 等待搜索结果区域加载完成
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "rso"))
        )
        # 获取所有搜索结果链接
        search_results = driver.find_elements(By.CSS_SELECTOR, "#rso a[href]")
        for link in search_results:
            href = link.get_attribute("href")
            if href:
                for site, identifier in urls.items():
                    if identifier in href and not links_dict[site]:
                        links_dict[site] = href
                        print(f"找到 {site} 的链接：{href}")
            # 如果所有链接都已找到，提前退出循环
            if all(links_dict.values()):
                break
        return links_dict
    except TimeoutException:
        print("结果区域加载超时")
        return links_dict
    except Exception as e:
        print(f"解析失败: {e}")
        return links_dict

def open_matched_website(links_dict: dict, save_path: str) -> bool:
    sites_order = ["yande", "danbooru", "gelbooru"]
    processed = False
    # 定义保存函数的字典
    save_functions = {
        "yande": save_yande_image,
        "danbooru": save_danbooru_image,
        "gelbooru": save_gelbooru_image
    }
    for site in sites_order:
        link = links_dict.get(site)
        if link:
            try:
                print(f"尝试处理 {site} 链接: {link}")
                driver.get(link)
                save_func = save_functions.get(site)
                if save_func and callable(save_func):
                    result = save_func(save_path, 15)
                else:
                    print(f"未找到 {site} 的保存函数")
                    result = False
                if result:
                    processed = True
                    break
                else:
                    print(f"{site} 处理失败，尝试下一个站点")
            except Exception as e:
                print(f"处理 {site} 时发生错误: {e}")
    return processed

def save_yande_image(save_path: str,timeout: int = 15) -> bool:
    # 等待页面主要内容加载完成
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '#image'))
    )
    try:
        status_element = driver.find_element(By.CSS_SELECTOR, '#post-view > div.status-notice')
        status_text = status_element.text.strip()
        print(f"状态通知：{status_text}")
        if any(keyword in status_text.lower() for keyword in ["删除", "deleted", "刪除"]):
            print("作品已被删除。")
            return False
    except NoSuchElementException:
        pass # 未找到状态通知元素，继续执行
    except Exception as e:
        print(f"检查通知时发生错误：{e}")
        return False
    try:
        image_link = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#resized_notice > a.highres-show"))
        )
        image_url = image_link.get_attribute('href')
        print("获取到原始尺寸图片的链接。")
    except (TimeoutException, NoSuchElementException):
        print("未找到原始尺寸的链接，尝试获取默认图片。")
        try:
            # 获取默认显示的图片
            image = WebDriverWait(driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#image"))
            )
            image_url = image.get_attribute('src')
            print("获取到默认图片的链接。")
        except (TimeoutException, NoSuchElementException):
            print("未找到图片元素，下载失败。")
            return False
    except Exception as e:
        print(f"获取图片链接时发生错误：{e}")
        return False
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        # 处理文件名
        image_name = os.path.basename(urlparse(image_url).path)
        image_name = urllib.parse.unquote(image_name)
        image_name = re.sub(r'[\\/*?:"<>|]', "", image_name)
        full_path = os.path.join(save_path, image_name)
        with open(full_path, 'wb') as file:
            file.write(response.content)
        print(f"图片已成功下载，保存为：{image_name}")
        return True
    except Exception as e:
        print(f"下载或保存图片时发生错误：{e}")
        return False

def save_danbooru_image(save_path: str, timeout: int = 15) -> bool:
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.ID, 'image'))
    )
    file_name = None
    try:
        first_image_link = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div/div/section/div[1]/div/div/div/article[1]/div/a'))
        )
        first_image_link.click()
    except Exception:
        print("未找到第一张")
    # try:
    #     source_link = WebDriverWait(driver, 2).until(
    #         EC.presence_of_element_located((By.CSS_SELECTOR, "#post-info-source > a:nth-child(1)"))
    #     )
    #     href = source_link.get_attribute('href')
    #     if "pixiv.net" in href:
    #         match = re.search(r'\d+$', href)
    #         if match:
    #             file_name = match.group()
    #             print(f"找到 Pixiv ID: {file_name}")
    #         else:
    #             print("未能从链接中提取出 ID")
    # except (TimeoutException, NoSuchElementException):
    #     print("未找到 Pixiv 链接")
    try:
        image_link = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#image-resize-notice > a"))
        )
        image_url = image_link.get_attribute('href')
        print("获取到原始尺寸图片的链接。")
    except (TimeoutException, NoSuchElementException):
        print("未找到原始尺寸的链接，尝试获取默认图片。")
        try:
            # 获取默认显示的图片
            image = WebDriverWait(driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#image"))
            )
            image_url = image.get_attribute('src')
            print("获取到默认图片的链接。")
        except (TimeoutException, NoSuchElementException):
            print("未找到图片元素，下载失败。")
            return False
    except Exception as e:
        print(f"获取图片链接时发生错误：{e}")
        return False
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        # 处理文件名
        image_name = os.path.basename(urlparse(image_url).path)
        image_name = urllib.parse.unquote(image_name)
        image_name = re.sub(r'[\\/*?:"<>|]', "", image_name)# 移除文件名中的非法字符
        full_path = os.path.join(save_path, image_name)

        # if file_name is not None:
        #     full_path=os.path.join(save_path,file_name+'_p0.'+image_name.split('.')[1])
        with open(full_path, 'wb') as file:
            file.write(response.content)
        print(f"图片已成功下载，保存到：{full_path}")
        return True
    except HTTPError as e:
            print(f"下载失败，状态码：{response.status_code}")
            return False
    except Exception as e:
            print(f"保存图片时发生错误：{e}")
            return False
    
def save_gelbooru_image(save_path: str, timeout: int = 15) -> bool:
    # try:
    #     file_name=None
    #     source_link = WebDriverWait(driver, timeout).until(
    #         EC.presence_of_element_located((By.CSS_SELECTOR, "section#tag-list a[href*='pixiv.net']"))
    #     )
    #     href = source_link.get_attribute('href')
    #     if "pixiv.net" in href:
    #         match = re.search(r'\d+$', href)
    #         if match:
    #             file_name = match.group()
    #             print(f"找到 Pixiv ID: {file_name}")
    #         else:
    #             print("未能从链接中提取出 Pixiv ID")
    #     else:
    #         print("链接不包含 pixiv.net")
    # except (TimeoutException, NoSuchElementException):
    #     print("未找到 Pixiv 链接")
    try:
        full_size_button=WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#resize-link > a"))
        )
        full_size_button.click()
    except Exception:
        print("未找到显示原始尺寸对应的按钮")
    time.sleep(1)
    image = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "image"))
    )
    image_url = image.get_attribute('src')
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        # 处理文件名
        image_name = os.path.basename(urlparse(image_url).path)
        image_name = urllib.parse.unquote(image_name)
        image_name = re.sub(r'[\\/*?:"<>|]', "", image_name)  # 移除非法字符
        full_path = os.path.join(save_path, image_name)

        # if file_name is not None:
        #     # 使用 Pixiv ID 作为文件名
        #     _, ext = os.path.splitext(image_name)
        #     image_name = f"{file_name}_p0{ext}"
        #     full_path = os.path.join(save_path, image_name)
        with open(full_path, 'wb') as file:
            file.write(response.content)
        print(f"图片已成功下载，保存到：{full_path}")
        return True
    except HTTPError as e:
            print(f"下载失败，状态码：{response.status_code}")
            return False
    except Exception as e:
            print(f"保存图片时发生错误：{e}")
            return False

def safe_move(src_path, dest_folder):
    file_name = os.path.basename(src_path)
    dest_path = os.path.join(dest_folder, file_name)
    base, ext = os.path.splitext(file_name)
    count = 1
    while os.path.exists(dest_path):
        new_file_name = f"{base}_{count}{ext}"
        dest_path = os.path.join(dest_folder, new_file_name)
        count += 1
    shutil.move(src_path, dest_path)
    return dest_path

if __name__ == "__main__":
    try:
        folders = [
            r"path_to_image_you_want_to_search",
            r"path_to_image_already_searched",
            r"path_to_image_found",
            r"path_to_image_not_found"
        ]
        for folder in folders:
            os.makedirs(folder, exist_ok=True)
        files = glob.glob(os.path.join(folders[0], "*.*"))
        images = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
        for idx, image_path in enumerate(images, 1):
            print(f"\n正在处理图片 ({idx}/{len(images)}): {os.path.basename(image_path)}")
            try:
                if not google_image_search(image_path, 20): raise Exception("图片未找到")# 执行搜索
                links = image_locate()# 获取链接
                # print("匹配结果:", links)
                if open_matched_website(links,folders[2]):
                    safe_move(image_path, folders[1])  # 移动到已搜索
                    print(f"{image_path} 处理完成")
                else:
                    safe_move(image_path, folders[3])  # 移动到未找到
                    print(f"{image_path} 未找到")
            except Exception as e:
                print(f"处理图片时发生错误: {e}")
                safe_move(image_path, folders[3])  # 异常情况移动图片至未找到
    finally:
        # driver.quit()
        pass