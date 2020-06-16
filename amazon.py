from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver
from lxml import etree
import pymysql
import requests
import datetime
import time
import sys


# 数据库连接和参数
connection = pymysql.connect(
	host = "localhost",
	user = "root",
	password = "root1234",
	db = "amazon",
	charset = "utf8mb4"
)
# 图片保存文件夹的绝对路径
imageFolder = "C:/Users/ASUS/Desktop/Amazon/image/"
# 启动个人配置的Chrome浏览器

option = webdriver.ChromeOptions()
option.add_argument("--user-data-dir="+
r"C:/Users/ASUS/AppData/Local/Google/Chrome/User Data/")
option.add_argument("--ignore-certificate-errors")
driver = webdriver.Chrome(chrome_options=option)

def save_log(source_from, error_message, function_name, line_number):
	pass
	# try:
	# 	with connection.cursor() as cursor:
	# 		error_message = str(error_message).replace("'", "\'")
	# 		sql = '''insert into error_log (source_from, error_message, function_name, line_number, add_time)values(
	# 		"%s","%s","%s",%d,now())''' % (source_from, error_message, function_name, line_number)
	# 		cursor.execute(sql)
	# 		connection.commit()
	# except Exception as e:
	# 	print('>>>>>', e)

def setChrome():
	'''
	因为浏览器打开亚马逊网站的默认收货地址为中国，影响sellers的判断
	所以此方法用于将收货地址改为10114邮编的纽约
	(由于可以启用个人配置的浏览器，此方法弃用)
	'''
	driver.get("https://www.amazon.com/")
	time.sleep(2)
	element = driver.find_element_by_xpath("//div[@id='nav-global-location-slot']/span/a")
	ActionChains(driver).click(element).perform()
	time.sleep(2)
	input_element = driver.find_element_by_xpath("//input[contains(@class, 'GLUX_Full_Width')]")
	button_element = driver.find_element_by_xpath("//span[@id='GLUXZipUpdate-announce']")
	ActionChains(driver).send_keys_to_element(input_element, "10114").click(button_element).perform()
	time.sleep(2)
	element = driver.find_element_by_xpath("//div[@class='a-popover-footer']//input[@id='GLUXConfirmClose']")
	ActionChains(driver).click(element).perform()
	time.sleep(4)

def findRank(page_source, asin):
	'''
	在网页源代码中查找商品的排名信息
	'''
	try:
		trs = page_source.xpath("//table[@id='productDetails_detailBullets_sections1']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Best Sellers Rank":
				ranks = tr.xpath("./td//text()")
				break
		result = []
		for i in ranks:
			if i.strip() and "See Top 100" not in i:
				result.append(i.strip())
		result = ' '.join(result)
		result = result.replace("(", "")
		result = result.replace(")", "")
		result = result.split("#")
		ranks = []
		for i in result:
			if i.strip():
				rank = i.strip().split("in")
				if len(rank) > 2:
					rank = [rank[0], 'in'.join(rank[1:])]
				ranks.append([i.strip() for i in rank])
		ranks = [[i[0].replace(",", ""), i[1]] for i in ranks]
		return ranks
	except Exception as e:
		save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
	try:
		ranks = page_source.xpath("//table[@id='productDetailsTable']//div[@class='content']/ul/li[@id='SalesRank']//text()")
		result = []
		for i in ranks:
			if i.strip() and "Amazon Best Sellers Rank" not in i and "See Top 100" not in i and "{" not in i and "}" not in i:
				result.append(i.strip())
		result = ' '.join(result)
		result = result.replace("(", "")
		result = result.replace(")", "")
		result = result.split("#")
		ranks = []
		for i in result:
			if i.strip():
				rank = i.strip().split("in")
				if len(rank) > 2:
					rank = [rank[0], 'in'.join(rank[1:])]
				ranks.append([i.strip() for i in rank])
		return ranks
	except Exception as e:
		save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
	try:
		ranks = page_source.xpath("//div[@id='detail-bullets']/table//div[@class='content']/ul/li[@id='SalesRank']//text()")
		result = []
		for i in ranks:
			if i.strip() and "Amazon Best Sellers Rank" not in i and "See Top 100" not in i and "{" not in i and "}" not in i:
				result.append(i.strip())
		result = ' '.join(result)
		result = result.replace("(", "")
		result = result.replace(")", "")
		result = result.split("#")
		ranks = []
		for i in result:
			if i.strip():
				rank = i.strip().split("in")
				if len(rank) > 2:
					rank = [rank[0], 'in'.join(rank[1:])]
				ranks.append([i.strip() for i in rank])
		return ranks
	except Exception as e:
		save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
	return []

def findCatalog(page_source, asin):
	'''
	在网页源代码中查找商品所属类别情况
	'''
	try:
		catalog = page_source.xpath("//div[@id='wayfinding-breadcrumbs_feature_div']/ul/li/span/a/text()")
		return [i.strip() for i in catalog]
	except Exception as e:
		save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
	return []

def findBrand(page_source, asin):
	'''
	在网页源代码中查找商品的品牌名称
	'''
	try:
		brand = page_source.xpath("//a[@id='bylineInfo']/text()")[0]
		return brand
	except Exception as e:
		save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
	return ""

def findSellers(page_source, asin):
	'''
	在网页源代码中查找并判断商品的销售方式
	'''
	try:
		info = page_source.xpath("//div[@id='merchant-info']/text()")
		sellers = "".join([i.strip() for i in info])
		if "Ships from and sold by Amazon" in sellers:
			return "AMZ"
		if "Ships from and sold by" in sellers:
			return "FBM"
		if "Sold by" in sellers:
			return "FBA"
		return sellers
	except Exception as e:
		save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
	return ""

def findSize(page_source, asin):
	'''
	在网页源代码中查找商品尺寸大小
	'''
	try:
		trs = page_source.xpath("//table[@id='productDetails_detailBullets_sections1']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Product Dimensions" or th.strip() == "Package Dimensions":
				size = tr.xpath("./td//text()")[0]
				return size.strip()
	except Exception as e:
		save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
	try:
		trs = page_source.xpath("//table[@id='productDetails_techSpec_section_1']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Product Dimensions" or th.strip() == "Package Dimensions":
				size = tr.xpath("./td//text()")[0]
				return size.strip()
	except Exception as e:
		save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
	try:
		trs = page_source.xpath("//table[@id='productDetails_techSpec_section_2']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Product Dimensions":
				size = tr.xpath("./td//text()")[0]
				return size.strip()
	except Exception as e:
		save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
	try:
		trs = page_source.xpath("//table[@class='a-bordered']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./td[1]/p/strong/text()")[0]
			if th.strip() == "Size":
				size = tr.xpath("./td[2]/p/text()")[0]
				return size.strip()
	except Exception as e:
		save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
	return ""

def findWeight(page_source, asin):
	'''
	在网页源代码中查找商品重量信息
	'''
	try:
		trs = page_source.xpath("//table[@id='productDetails_detailBullets_sections1']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Item Weight":
				weight = tr.xpath("./td//text()")[0]
				return weight.strip()
	except Exception as e:
		save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
	try:
		uls = page_source.xpath("//table[@id='productDetailsTable']//div[@class='content']/ul")
		for ul in uls:
			th = ul.xpath("./li/b/text()")[0]
			if th.strip() == "Shipping Weight:":
				weight = ul.xpath("./li/text()")[0]
				weight = weight.replace("(", "")
				return weight.strip()
	except Exception as e:
		save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
	try:
		trs = page_source.xpath("//table[@id='productDetails_techSpec_section_1']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Item Weight":
				weight = tr.xpath("./td//text()")[0]
				return weight.strip()
	except Exception as e:
		save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
	try:
		trs = page_source.xpath("//table[@id='productDetails_techSpec_section_2']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Item Weight":
				weight = tr.xpath("./td//text()")[0]
				return weight.strip()
	except Exception as e:
		save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
	try:
		trs = page_source.xpath("//table[@class='a-bordered']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./td[1]/p/strong/text()")[0]
			if th.strip() == "Weight":
				weight = tr.xpath("./td[2]/p/text()")[0]
				return weight.strip()
	except Exception as e:
		save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
	try:
		lis = page_source.xpath("//div[@id='detail-bullets']/table//div[@class='content']/ul/li")
		for li in lis:
			b = li.xpath("./b/text()")[0]
			if "Shipping Weight" in b.strip():
				weight = li.xpath("./text()")[0].replace("(", "")
				return weight.strip()
	except Exception as e:
		save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
	return ""

def findReleaseData(page_source, asin):
	'''
	在网页源代码中查找商品的上架日期
	'''
	monthDict = {
		"January" : "1",
		"February" : "2",
		"March" : "3",
		"April" : "4",
		"May" : "5",
		"June" : "6",
		"July" : "7",
		"August" : "8",
		"September" : "9",
		"October" : "10",
		"November" : "11",
		"December" : "12"
	}
	try:
		trs = page_source.xpath("//table[@id='productDetails_detailBullets_sections1']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Date First Available":
				release_data = tr.xpath("./td//text()")[0]
				month, day, year = release_data.strip().replace(",", " ").split()
				return year+"-"+monthDict[month]+"-"+day
	except Exception as e:
		save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
	try:
		trs = page_source.xpath("//table[@id='productDetails_techSpec_section_1']/tbody/tr")
		for tr in trs:
			th = tr.xpath("./th/text()")[0]
			if th.strip() == "Date First Available":
				release_data = tr.xpath("./td//text()")[0]
				month, day, year = release_data.strip().replace(",", " ").split()
				return year+"-"+monthDict[month]+"-"+day
	except Exception as e:
		save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
	return ""

def getPageSource(url, mod=0):
	'''
	获取指定url链接页面的源代码
	'''
	start_time = time.time()
	driver.get(url)
	try:
		if mod == 0:
			locator = (By.XPATH, "//ul[@id='zg_browseRoot']")
			WebDriverWait(driver, 6, 1).until(EC.presence_of_element_located(locator))
		if mod == 1:
			locator = (By.XPATH, "//div[@id='prodDetails']")
			WebDriverWait(driver, 6, 1).until(EC.presence_of_element_located(locator))
	except Exception as e:
		save_log(url, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
	try:
		element = driver.find_element_by_xpath("//a[contains(text(), 'Try different image')]")
		ActionChains(driver).click(element).perform()
		return getPageSource(url, mod)
	except Exception as e:
		pass
	end_time = time.time()
	with open("time.txt", "a") as f:
		f.write(str(end_time-start_time)+"\n")
	# time.sleep(1)
	page_source = driver.page_source
	page_source = etree.HTML(page_source)
	return page_source

def fullProductInfo(page_source, asin):
	'''
	首先从页面源代码中查找商品的品牌名称、销售方式、尺寸大小、重量、上架日期和排名
	然后根据商品的asin将处排名外的信息保存到product表中，排名信息保存到ranking表中
	'''
	brand = findBrand(page_source, asin)
	brand = brand.replace("'", r"\'")
	print('\n品牌名称:', brand)
	sellers = findSellers(page_source, asin)
	print('销售方式:', sellers)
	size = findSize(page_source, asin)
	size = size.replace("'", r"\'")
	print('尺寸:', size)
	weight = findWeight(page_source, asin)
	weight = weight.replace("'", r"\'")
	print('重量:', weight)
	release_data = findReleaseData(page_source, asin)
	if release_data:
		release_data = "'%s'" % release_data
	else:
		release_data = "NULL"
	print('上架日期:', release_data)
	ranks = findRank(page_source, asin)
	print('排名:', ranks)
	if all([brand, sellers, size, weight, release_data]):
		fulled = 1
	else:
		fulled = 0
	try:
		with connection.cursor() as cursor:
			sql = '''update product set brand='%s',sellers='%s',size='%s',
			weight='%s',release_data=%s,fulled=%d,update_time=now() where asin='%s' '''% (
			brand,sellers, size, weight, release_data, fulled, asin)
			cursor.execute(sql)
			for rank in ranks:
				sql = '''insert into ranking(asin, rank_name, rank_number,
				add_time)values('%s','%s',%d,now())''' % (asin, rank[1], int(rank[0]))
				cursor.execute(sql)
	except Exception as e:
		print("^^^^^^", e)
		save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
	connection.commit()

def crwalList(page_source, catalog):
	'''
	获取商品列表中商品的链接、asin、图片链接、评论分数、评论人数、价格和标题，
	先根据asin查询product表中是否已存在此商品，再将不存在的商品信息保存到product表
	'''
	product_list = page_source.xpath("//ol[@id='zg-ordered-list']/li")
	for i, p in enumerate(product_list):
		try:
			address = p.xpath(".//span[contains(@class, 'zg-item')]/a[@class='a-link-normal']/@href")[0]
			address = "https://www.amazon.com" + address
			words = address.split("/")
			asin = words[words.index("dp") + 1]
			image = p.xpath(".//img/@src")[0]
		except Exception as e:
			save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
		try:
			review_score = p.xpath(".//div[contains(@class, 'a-icon-row')]/a[1]/@title")[0]
			review_score = float(review_score.split("out")[0])
		except Exception as e:
			review_score = 0
			save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
		try:
			review_number = p.xpath(".//div[contains(@class, 'a-icon-row')]/a[2]/text()")[0]
			review_number = review_number.replace(",", "")
			review_number = int(review_number)
		except Exception as e:
			review_number = 0
			save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
		try:
			price = p.xpath(".//span[@class='p13n-sc-price']/text()")
			if len(price) > 1:
				multiple = 1
			else:
				multiple = 0
			price = float(price[0].replace(",", "").strip()[1:])
		except Exception as e:
			price = -1
			save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
		try:
			title = p.xpath(".//div[@class='p13n-sc-truncated']/@title")[0]
		except Exception as e:
			title = p.xpath(".//div[@class='p13n-sc-truncated']/text()")[0]
			save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
		title = title.replace("'", r"\'")
		catalog = [i.replace("'", r"\'") for i in catalog]
		try:
			with connection.cursor() as cursor:
				sql = '''select asin from product where asin='%s' ''' % asin
				result = cursor.execute(sql)
				if result != 1:
					sql = '''insert into product (asin, address, title, image,
					review_number, review_score, price, multiple, level, catalog, add_time, update_time)
					values('%s', '%s', '%s', '%s', %d, %f, %f, %d, %d, '%s', now(), now())''' % (asin,
					address, title,image, review_number, review_score, price, multiple, len(catalog), ">".join(catalog))
					cursor.execute(sql)
		except Exception as e:
			save_log(asin, e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)
		connection.commit()

def crawCatalog(url, max_level=2, now_level=0):
	'''
	递归的爬取类别目录和目录商品
	'''
	if max_level == now_level:
		return
	page_source = getPageSource(url)
	catalog = []
	ul = page_source.xpath("//ul[@id='zg_browseRoot']")[0]
	while True:
		r = ul.xpath("./ul")
		if r:
			catalog.append(" ".join(ul.xpath("./li//text()")).replace("‹", "").strip())
			ul = r[0]
		else:
			break
	select_span = ul.xpath("./li/span[@class='zg_selected']/text()")
	if select_span:
		catalog.append(select_span[0].strip())
	print(catalog)
	crwalList(page_source, catalog)
	next_page_url = page_source.xpath("//li[@class='a-last']/a/@href")[0]
	page_source = getPageSource(next_page_url)
	crwalList(page_source, catalog)
	if select_span:
		return
	next_catalog_urls = ul.xpath("./li/a/@href")
	for url in next_catalog_urls:
		crawCatalog(url, max_level, now_level=now_level+1)

def downloadImage():
	'''
	根据商品的图片链接下载保存到指定文件夹
	'''
	try:
		with connection.cursor() as cursor:
			sql = "select name, link from image where download is NULL limit 10"
			cursor.execute(sql)
			result = cursor.fetchall()
			for image in result:
				print(image[1])
				try:
					response = requests.get(image[1], timeout=5)
				except Exception as e:
					continue
				print("get response")
				with open(imageFolder+image[0], "wb") as f:
					for chunk in response.iter_content(chunk_size=128):
						f.write(chunk)
				print("downloadImage")
				sql = "update image set download=1 where name='%s'" % image[0]
				cursor.execute(sql)
				print("save on db")
			connection.commit()
	except Exception as e:
		print(e)
		save_log(image[0], e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)

def resultOfHTML():
	with connection.cursor() as cursor:
		sql = '''select image,asin,review_number,review_score,price,level,catalog,title,brand,sellers,
		size,weight,address,release_data from product where fulled=1 limit 50'''
		cursor.execute(sql)
		result = cursor.fetchall()
		with open("%s.html"%datetime.datetime.now().strftime("%Y-%m-%d"), "w", encoding="utf-8") as f:
			f.write('''<table border="1" cellpadding="0" cellspacing="0"><thead><td>图片</td><td>编号</td><td>评论人数</td><td>评论分数</td>
			<td>价格</td><td>类目层级</td><td>类别目录</td><td>标题</td><td>品牌名称</td><td>销售方式</td>
			<td>尺寸</td><td>重量</td><td>页面地址</td><td>上架日期</td></thead><tbody>''')
			for p in result:
				f.write('''<tr><td><img src="%s"></td><td>%s</td><td>%d</td><td>%.1f</td><td>%.2f</td><td>%d</td>
				<td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td><a href="%s"
				target="_blank">详情</a></td><td>%s</td></tr>''' % p)
			f.write("</tbody></table>")

def keepa():
	'''
	首先查询数据库中商品上架日期为空的商品，再通过keepa谷歌浏览器插件获取商品的上架日期，更新数据库
	'''
	with connection.cursor() as cursor:
		sql = "select address, asin from product where release_data is NULL"
		cursor.execute(sql)
		result = cursor.fetchall()
	try:
		for i in result:
			driver.get(i[0])
			time.sleep(5)
			driver.switch_to.frame('keepa')
			element = driver.find_element_by_xpath("//table[@class='legendTable']/tbody/tr[last()]/td[2]/table/tbody/tr[last()]/td[2]")
			days = int(element.text.split("(")[1].split("天")[0].strip())
			release_data = (datetime.datetime.now() + datetime.timedelta(days=-days)).strftime("%Y-%m-%d")
			print(i[1], release_data)
			with connection.cursor() as cursor:
				sql = "update product set release_data='%s' where asin='%s'" % (release_data, i[1])
				cursor.execute(sql)
			connection.commit()
	except Exception as e:
		save_log(i[1], e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)

def work1(urls):
	'''
	根据指定的url列表获取商品信息
	'''
	for url in urls:
		page_source = getPageSource(url)
		crwalList(page_source)

def work2():
	'''
	将product表中fulled字段为NULL的数据信息补充完整
	'''
	try:
		with connection.cursor() as cursor:
			sql = "select asin, address from product where fulled is NULL"
			cursor.execute(sql)
			result = cursor.fetchall()
			for i in result:
				page_source = getPageSource(i[1], mod=1)
				fullProductInfo(page_source, i[0])
	except Exception as e:
		print("======", e)
		save_log(i[0], e, sys._getframe().f_code.co_name, sys._getframe().f_lineno)


if __name__ == '__main__':
	urls = [
	"https://www.amazon.com/Best-Sellers-Electronics-TV-Accessories/zgbs/electronics/3230976011/ref=zg_bs_pg_2?_encoding=UTF8&pg=2"
	]
	url = "https://www.amazon.com/Best-Sellers/zgbs/wireless/ref=zg_bs_nav_0"
	# work1(urls)
	work2()
	# keepa()
	# crawCatalog(url)
	# resultOfHTML()
	# downloadImage()