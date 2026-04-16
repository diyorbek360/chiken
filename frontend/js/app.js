// app.js — Main entry point
(async function () {
  // ── Telegram WebApp init ──────────────────────────────────
  const tg = window.Telegram?.WebApp;
  if (tg) {
    tg.ready();
    tg.expand();
    tg.setHeaderColor("#87CEEB");
    tg.setBackgroundColor("#87CEEB");
  }

  // Extract user data from Telegram
  let telegramId = null;
  let username = null;
  let language = null;
  let referralCode = null;
  let initData = null;

  if (tg?.initDataUnsafe?.user) {
    const user = tg.initDataUnsafe.user;
    telegramId = user.id;
    username = user.username || user.first_name || null;
    language = user.language_code || navigator.language?.split("-")[0] || "en";
    initData = tg.initData;
  } else {
    // Dev/browser fallback
    telegramId = parseInt(localStorage.getItem("dev_tg_id") || "100000001");
    username = localStorage.getItem("dev_username") || "DevUser";
    language = navigator.language?.split("-")[0] || "ru";
    console.warn("Running in browser mode (no Telegram context)");
  }

  // Referral from start param
  const startParam = tg?.initDataUnsafe?.start_param || new URLSearchParams(location.search).get("start");
  if (startParam?.startsWith("ref_")) {
    referralCode = startParam.replace("ref_", "");
  }

  // Set i18n language
  i18n.setLang(language);

  // Auth API
  if (telegramId) {
    api.setAuth(telegramId, initData);
  }

  // Show loading screen
  ui.showScreen("loading");

  // Init game
  const { user, isNew, chickenAlive } = await game.init(
    telegramId, username, language, referralCode
  );

  // Override language from user profile
  if (user.language && user.language !== language) {
    i18n.setLang(user.language);
  }

  // Show game screen
  ui.showScreen("game");
  ui.renderFarmScene();
  ui.updateHUD();
  ui.renderNavButtons();

  // Tutorial for new players
  if (isNew || !user.tutorial_completed) {
    setTimeout(() => ui.startTutorial(), 800);
  }

  // Trader popup if active
  if (user.trader_active && user.tutorial_completed) {
    setTimeout(() => ui.showTraderPopup(), 1200);
  }

  // ── Back button ──────────────────────────────────────────
  if (tg) {
    tg.BackButton.onClick(() => {
      if (ui.currentScreen !== "game") {
        ui.showScreen("game");
        tg.BackButton.hide();
      }
    });
  }
})();

// ── Event Handlers ────────────────────────────────────────────

// Feeder: click + button
document.addEventListener("click", (e) => {
  // Close popups on backdrop click
  if (e.target.classList.contains("popup-overlay")) {
    ui.closeAllPopups();
  }
});

function onFeedClick() {
  if (game.state?.feed_bags <= 0) {
    // Show market popup
    ui.showPopup({
      emoji: "🌾",
      title: "Нет корма!",
      body: i18n.t("no_feed_error"),
      btns: [
        { label: i18n.t("go_to_market"), cls: "popup-btn-primary", action: () => { ui.closeAllPopups(); ui.showScreen("market"); } },
        { label: i18n.t("close_btn"), cls: "popup-btn-secondary", action: () => ui.closeAllPopups() },
      ]
    });
  } else {
    game.feedChickens();
  }
}

function onFeedMax() {
  // Use all feed bags
  game.feedChickens();
}

function onCollectEggs() {
  game.collectEggs();
}

function onNavMarket() {
  ui.showScreen("market");
  if (window.Telegram?.WebApp) Telegram.WebApp.BackButton.show();
}

function onNavLeaders() {
  ui.showScreen("leaders");
  if (window.Telegram?.WebApp) Telegram.WebApp.BackButton.show();
}

function onNavSettings() {
  ui.showScreen("settings");
  if (window.Telegram?.WebApp) Telegram.WebApp.BackButton.show();
}

function onBackToGame() {
  ui.showScreen("game");
  if (window.Telegram?.WebApp) Telegram.WebApp.BackButton.hide();
}

function onMarketPay() {
  ui.purchaseCart();
}

function onCloseMarket() {
  ui.showScreen("game");
}

function onTutorialNext() {
  ui.advanceTutorial();
}

function onHudBalanceClick() {
  const days = game.state?.days_until_trader ?? "?";
  ui.showToast(i18n.t("days_until_trader", { days }), "info");
}

function onHudBagsClick() {
  ui.showScreen("market");
}

function onSaveNickname() { ui.saveNickname(); }
function onSaveWallet() { ui.saveWallet(); }
function onRequestWithdraw() { ui.requestWithdraw(); }
function onCopyReferralLink() { ui.copyReferralLink(); }
function onLangChange(el) { ui.changeLang(el.value); }

function onClosePopup(id) {
  document.getElementById(id)?.classList.add("hidden");
}

function onTraderBuyChicken() { ui.traderBuyChicken(); }
function onTraderWithdraw() { ui.traderWithdraw(); }

function onOpenTrader() {
  if (game.state?.trader_active) ui.showTraderPopup();
}
