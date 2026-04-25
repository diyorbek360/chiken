
const API_BASE = window.location.hostname === "localhost"
  ? "http://localhost:8000/api/v1"
  : "/api/v1";

class ApiClient {
  constructor() {
    this.telegramId = null;
    this.initData = null;
  }

  setAuth(telegramId, initData) {
    this.telegramId = telegramId;
    this.initData = initData;
  }

  async _request(method, path, body = null) {
    const headers = { "Content-Type": "application/json" };
    if (this.initData) {
      headers["X-Init-Data"] = this.initData;
    } else if (this.telegramId) {
      headers["X-Init-Data"] = `debug:${this.telegramId}`;
    }

    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);

    try {
      const res = await fetch(`${API_BASE}${path}`, opts);
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Network error" }));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      return await res.json();
    } catch (e) {
      console.error(`API error [${method} ${path}]:`, e);
      throw e;
    }
  }

  get(path) { return this._request("GET", path); }
  post(path, body) { return this._request("POST", path, body); }
  patch(path, body) { return this._request("PATCH", path, body); }

  async initPlayer(telegramId, username, language, referralCode) {
    return this.post("/auth/init", {
      telegram_id: telegramId,
      username,
      language,
      referral_code: referralCode,
    });
  }

  async getMe() { return this.get("/me"); }

  async feed() { return this.post("/game/feed"); }
  async collect() { return this.post("/game/collect"); }
  async steal(victimUserId) { return this.post("/game/steal", { victim_user_id: victimUserId }); }
  async completeTutorial() { return this.post("/game/tutorial/complete"); }
  async completeMarketTutorial() { return this.post("/game/tutorial/market-complete"); }

  async getPrices() { return this.get("/shop/prices"); }
  async buyItem(item, quantity = 1) { return this.post("/shop/buy", { item, quantity }); }

  async getLeaderboard() { return this.get("/leaderboard"); }
  async getPlayerFarm(playerId) { return this.get(`/leaderboard/player/${playerId}`); }
  async updateNickname(nickname) { return this.patch("/settings/nickname", { nickname }); }
  async updateWallet(wallet_address) { return this.patch("/settings/wallet", { wallet_address }); }
  async updateLanguage(language) { return this.patch(`/settings/language?language=${language}`); }
  async getReferrals() { return this.get("/settings/referrals"); }

  async requestWithdrawal(amount) { return this.post("/withdraw/request", { amount }); }
  async getWithdrawHistory() { return this.get("/withdraw/history"); }
}

window.api = new ApiClient();
