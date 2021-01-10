################################
# download free music 
################################
# 1. init freesound()
# 2. login freesound()
# 3. Download freesound music
################################ 
# python執行引述輸入格式說明 [檔名.py] [tag or search] [搜尋文字] [起始下載數量(從1開始數)] [結尾下載數量(含最後一個)] [下載位置(最後面必須加'/')]
################################
import requests
from bs4 import BeautifulSoup
import os, sys
import freesound_value

class freesound():
    def __init__(self):
        # 把request都算在同一個session裡，我們第二次對登入頁面發request時，csrfmiddlewaretoken value才不會又重新產生。
        self.session = requests.Session()

        self.LOGIN_URL = "https://freesound.org/home/login/"

        #表頭-給予資訊，偽裝成瀏覽器
        self.headers = { 
            'Referer':'https://freesound.org/home/login/?next=/',
            # 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
        }

    def login_freesound(self,USERNAME,PASSWORD):
        # 登入freesound

        # Retrieve the CSRF token first
        self.session.get(self.LOGIN_URL)  # sets cookie
        if 'csrftoken' in self.session.cookies:
            # Django 1.6 and up
            csrftoken = self.session.cookies['csrftoken']
            print('登入回應 find csrftoken')
        else:
            # older versions
            csrftoken = self.session.cookies['csrf']
            print('登入回應 Not find csrftoken')

        #要Post的資訊
        data = {'csrfmiddlewaretoken' : csrftoken,
                'username': USERNAME,
                'password': PASSWORD,
                'next':'/',
                }
            
        # 以POST method登入
        result = self.session.post(self.LOGIN_URL,headers = self.headers,data=data)
        print('登入回應 status_code : %d' % result.status_code)

        return result #login page
    
    def saveHTMLfile(self,content,file_path):
        #儲存網頁到txt
        try :
            with open(file_path,'wb') as file_Obj:
                for diskStorage in content.iter_content(40960):
                    size = file_Obj.write(diskStorage)
                    # print(size)
                print("以 %s 儲存網頁HTML檔案成功" % file_path)
        except :
            print('儲存檔案失敗')

    def test_login_main(self,USERNAME,PASSWORD):
        result = self.login_freesound(USERNAME,PASSWORD)
        self.saveHTMLfile(result,'login_freesound.htm')

    def download_music(self,url,file_path): #下載音樂
        #先判斷file_path的資料夾是否建立
        folder = os.path.exists(file_path) #存在：True #不存在：False
        if not folder: #如果不存在，則建立新目錄
            os.makedirs(file_path)
            print('資料夾路徑建立成功')

        local_filename = url.split('/')[-1]
        # NOTE the stream=True parameter below
        with self.session.get(url,stream=True) as r:
            print("連線狀態:%d，正在下載 %s 中..." % (r.status_code,local_filename))
            r.raise_for_status()
            with open( file_path + local_filename , 'wb' ) as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    # If you have chunk encoded response uncomment if
                    # and set chunk_size parameter to None.
                    #if chunk: 
                    f.write(chunk)
        return local_filename

    def test_load_html(self,url): 
        # 用Get方法取得網頁內容
        print('load html url : %s' % url)
        result = self.session.get(url)
        print('status_code : %d' % result.status_code)
        return result

    def test_search_tag(self,tag):
        result = self.test_load_html('https://freesound.org/browse/tags/'+tag)
        self.saveHTMLfile(result,'freesound_tag.htm')
        return result

    def downloading_music(self,title_url,num_times,num,file_path): # 輸入URL下載音樂(型態網址,起始數,結尾數,下載檔案預存取位置)
        
        while(num_times < num):
            page_num = str(num_times // 15 + 1)

            try :
                response = self.session.get(title_url +'page='+ page_num +'#sound')

                soup = BeautifulSoup(response.text, "html.parser")
                result_bs4 = soup.find_all("div", class_="sound_filename", limit=15) # 找到搜尋結果頁面上每一個項目的音樂名稱內容

                start_flag = False
                for i, title in enumerate(result_bs4): 
                    # print(i) # 正在處理頁面上搜尋結果第幾個項目

                    if i == num_times % 15: #從num_times % 15開始
                        start_flag = True
                    
                    if start_flag == True:
                        file_num_href_url = title.select_one("a").get("href") # 找到搜尋結果頁面上每一個項目的 href 連結網址

                        try:
                            response2 = self.session.get('https://freesound.org' + file_num_href_url) # 進入連結網址找下載音樂的網址
                            soup2 = BeautifulSoup(response2.text, "html.parser") 
                            result_bs4_2 = soup2.find("div", id="download") # 找含有download項目的內容
                            file_href_url = result_bs4_2.select_one("a").get("href") # 找到音樂 href 下載網址
                            # print(file_href_url) 
                            
                            self.download_music('https://freesound.org' + file_num_href_url + 'download' + file_href_url, file_path) #下載音樂
                            
                            print(f'已經完成下載 {num_times+1}/{num} 個項目')
                        except (EOFError, KeyboardInterrupt):
                            sys.exit()
                        except:
                            print(f'下載失敗，跳過 {num_times+1}/{num} 項目')

                        num_times += 1
                        
                        if num_times >= num:
                            return "Download finish!"
                    # else:
                    #     print('還沒數到起始點，跳過')
            except (EOFError, KeyboardInterrupt):
                sys.exit()
            except :
                print(f'下載搜尋結果第{page_num}頁失敗，跳往下一頁')
                num_times += 15 # 直接跳下一頁
        
        return "Download finish!"

    def download_tag_music(self,tag,start_num,num,file_path): # 輸入Tag下載相關音樂(Tag字串,下載數量,下載檔案預存取位置)
        return self.downloading_music('https://freesound.org/browse/tags/'+ tag + '/?',start_num,num,file_path)


    def download_search_music(self,search,start_num,num,file_path): # 輸入Tag下載相關音樂(Tag字串,下載數量,下載檔案預存取位置)
        return self.downloading_music('https://freesound.org/search/?q='+ search + '&',start_num,num,file_path)



if __name__ == '__main__':
    M = freesound()
    # M.test_login_main('12345678@yahoo.com.tw','12345678')
    M.login_freesound(freesound_value.USERNAME,freesound_value.PASSWOED)
    # print(M.download_music('https://freesound.org/people/florianreichelt/sounds/459977/download/459977__florianreichelt__soft-wind.mp3'),'music_download/')
    # M.test_search_tag('ambiance') # test
 
    # python執行引述輸入格式 [檔名.py] [tag or search] [搜尋文字] [起始下載數量(從1開始)] [結尾下載數量(含最後一個)] [下載位置(最後面必須加'/')]
    if int(sys.argv[3]) >= int(sys.argv[4]):
        print('[輸入格式錯誤] 起始數量必須小於結束數量')
        sys.exit() 

    if sys.argv[1] == 'tag':
        print(M.download_tag_music(sys.argv[2],int(sys.argv[3])-1,int(sys.argv[4]),sys.argv[5]))
    elif sys.argv[1] == 'search':
        print(M.download_search_music(sys.argv[2],int(sys.argv[3])-1,int(sys.argv[4]),sys.argv[5]))    
    else :
        print('[輸入格式錯誤] 第一個參數請填寫搜尋型態(tag或search)')