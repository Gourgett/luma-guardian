import google.generativeai as genai
import os
import json
import time
import random

# ==============================================================================
#  LUMA ORACLE v2.5 [FAIL-OPEN EDITION]
#  Logic: If AI is online -> Use AI Advice.
#         If AI is busy   -> BYPASS AND TRADE (Trust Technicals).
# ==============================================================================

class Oracle:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = None
        self.last_call = 0
        self.failures = 0
        
        # [CONFIGURATION]
        # If True, we trade even if the AI is broken/busy.
        self.FAIL_OPEN = True
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            except:
                print("xx ORACLE INIT FAILED. Running in Bypass Mode.")

    def consult(self, coin, setup_type, price, context):
        # 1. Check if configured
        if not self.model:
            return True # Bypass if no key
            
        # 2. Rate Limit Throttling (Client Side)
        elapsed = time.time() - self.last_call
        if elapsed < 2.0:
            time.sleep(2.0 - elapsed)

        try:
            # 3. Construct the Prompt
            prompt = f"""
            ACT AS A TRADING VALIDATOR.
            Asset: {coin}
            Price: {price}
            Setup: {setup_type}
            Context: {context}

            Task: Validating a high-frequency trade signal.
            Output: Respond with exactly ONE word: 'YES' or 'NO'.
            Logic: If the setup is technically sound (even slightly), say YES. Only say NO if it is an obvious error.
            """
            
            # 4. The API Call
            response = self.model.generate_content(prompt)
            self.last_call = time.time()
            self.failures = 0
            
            clean_response = response.text.strip().upper()

            if "YES" in clean_response:
                return True
            elif "NO" in clean_response:
                print(f">> 🛡️ ORACLE: Blocked {coin} (AI Rejected Setup)")
                return False
            else:
                return True # Ambiguous response -> Allow Trade
            
        except Exception as e:
            # 5. THE CRITICAL FIX: HANDLE RATE LIMITS
            error_msg = str(e).lower()
            
            # If Rate Limit (429) -> ALLOW THE TRADE
            if "429" in error_msg or "quota" in error_msg or "rate limit" in error_msg:
                if self.FAIL_OPEN:
                    print(f">> ⚡ ORACLE BUSY (Rate Limit). BYPASSING -> EXECUTE TRADE.")
                    return True
                else:
                    return False
            
            # Handle other errors (Network, etc) -> ALLOW TRADE
            print(f">> ⚠️ ORACLE ERROR: {e}. Bypassing check.")
            return True
