import os
import requests

chat_language = os.getenv("INIT_LANGUAGE", default = "zh")

MSG_LIST_LIMIT = int(os.getenv("MSG_LIST_LIMIT", default = 7))
LANGUAGE_TABLE = {
  "zh": "哈囉！",
  "en": "Hello!"
}

# Edge Config URL
EDGE_CONFIG_URL = os.getenv("EDGE_CONFIG")

# 使用環境變數來設置 AI_GUIDELINES，如果沒有設置則使用默認值
AI_GUIDELINES = os.getenv("AI_GUIDELINES", '你是一個AI助教，會用蘇格拉底教學法代替老師初步回應，如果有需要會提醒學生跟老師確認')

class Prompt:

    def __init__(self):
        """
        初始化時嘗試從 Edge Config 獲取 line_prompt，
        如果失敗則回退到預設的 AI_GUIDELINES。
        """
        # 初始化 msg_list
        self.msg_list = []

        # 嘗試從 Edge Config 獲取 line_prompt
        self.default_guideline = self.fetch_edge_config_item("line_prompt")

        # 初始化系統訊息
        self.msg_list.append(
            {
                "role": "system",
                "content": f"{LANGUAGE_TABLE[chat_language]}, {self.default_guideline}"
            }
        )

    def add_msg(self, new_msg):
        if len(self.msg_list) >= MSG_LIST_LIMIT:
            # 確保不刪除第一個系統訊息，改為刪除第二個訊息
            self.msg_list.pop(1)
        self.msg_list.append({"role": "user", "content": new_msg})

    def generate_prompt(self):
        return self.msg_list

    def reinit_(self, new_guideline=None):
        """
        重新初始化系統訊息，允許外部更新指導方針。
        """
        # 更新 default_guideline
        if new_guideline:
            self.default_guideline = new_guideline
        # 重新初始化系統訊息
        self.msg_list[0] = {
            "role": "system",
            "content": f"{LANGUAGE_TABLE[chat_language]}, {self.default_guideline}"
        }
        # 清空所有非系統訊息
        self.msg_list = [self.msg_list[0]]

    @staticmethod
    def fetch_edge_config_item(key):
        """
        從 Edge Config 獲取指定的配置項目。如果失敗或不存在，返回 AI_GUIDELINES。
        """
        try:
            if not EDGE_CONFIG_URL:
                raise ValueError("EDGE_CONFIG 環境變數未設置")

            # 發送請求到 Edge Config API
            response = requests.get(f"{EDGE_CONFIG_URL}")
            response.raise_for_status()  # 確保請求成功

            # 獲取 JSON 數據
            data = response.json()

            # 確認 key 是否存在
            if key in data:
                return data[key]
            else:
                raise KeyError(f"Key '{key}' 不存在於 Edge Config 中")
        except requests.exceptions.RequestException as e:
            print(f"Error: 無法從 Edge Config 獲取數據: {e}")
        except KeyError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"未知錯誤: {e}")

        # 返回預設值作為保險
        return AI_GUIDELINES