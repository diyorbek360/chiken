// i18n.js — Multilingual support (10 languages)
const TRANSLATIONS = {
  ru: {
    feed_btn: "КОРМИТЬ",
    collect_btn: "Собрать яйца",
    market_title: "РЫНОК",
    leaders_title: "ЛИДЕРЫ",
    settings_title: "НАСТРОЙКИ",
    day_label: "День",
    no_feed_error: "Нет корма! Купите в магазине.",
    chicken_died_title: "Курица умерла 😢",
    chicken_died_body: "Ваша курица умерла от голода.\nЗаработанные деньги сохранены!",
    restart_btn: "Начать заново",
    trader_title: "Торговец прибыл! 🎪",
    buy_chicken_discount: "Купить курицу со скидкой 20%",
    withdraw_money: "Вывести деньги на кошелёк",
    no_glove_popup: "У вас нет перчатки вора. Купите её в магазине!",
    go_to_market: "В магазин",
    dog_protection: "Собака охраняет этот двор! 🐕 Ничего украсть нельзя.",
    already_stolen: "Яйца уже были украдены сегодня. Приходи завтра!",
    tutorial_1: "Твоя курица несёт золотые яйца! 🐔\nЧтобы начать, добавь корм в кормушку.",
    tutorial_2: "Отлично! Теперь у твоей курицы есть еда на 24 часа.\nКаждый день нужно добавлять корм. Чем больше куриц — тем больше еды они потребляют!",
    tutorial_3: "Следи за запасом корма в верхнем углу. Корм можно купить в магазине или получить за каждого приглашённого друга. За тебя действует бонус — каждый друг приносит 3 единицы корма!",
    tutorial_4: "В магазине ты можешь купить корм, дополнительных куриц или другие улучшения для своей фермы.",
    tutorial_5: "В игре можно воровать чужие яйца! Если хочешь защититься — найми сторожевого пса в магазине. 🐕",
    tutorial_6: "Каждые 10 дней на ферму приезжает торговец. Ты можешь продать яйца и вывести деньги на кошелёк! 💰",
    next_btn: "Далее →",
    close_btn: "Закрыть",
    got_it: "Понятно!",
    days_until_trader: "До торговца {days} дн.",
    wallet_saved: "Кошелёк сохранён! ✓",
    no_wallet: "Привяжите TON кошелёк в настройках для вывода средств.",
    withdraw_pending: "Запрос принят! Статус вывода — в истории.",
    invite_msg: "Моя курица несёт золотые яйца 🐔 Заведи свою! ",
    death_warning: "⚠️ Осталось 2 часа! Покорми курицу!",
    low_feed_warning: "🛒 Остался 1 мешок корма!",
    balance_label: "Баланс",
    nickname_label: "Ник",
    wallet_label: "Номер TON кошелька",
    invite_label: "Пригласить друга",
    friends_count: "Приглашённых друзей:",
    withdraw_history: "ИСТОРИЯ ВЫВОДОВ",
    auth_label: "Авторизация",
    lang_label: "язык",
    already_owned: "Куплено ✓",
    buy_btn: "Купить",
    total_label: "Итого:",
    pay_btn: "ОПЛАТИТЬ",
    list_of_leaders: "СПИСОК ЛИДЕРОВ",
    list_of_players: "СПИСОК ИГРОКОВ",
    score_label: "очков",
    steal_btn: "Украсть яйца",
    chickens_label: "Кур:",
    feed_bags_label: "Мешков корма",
    yes_btn: "ДА",
    no_btn: "НЕТ",
    market_btn: "РЫНОК",
    ok_btn: "OK",
    chicken_item: "курица",
    glove_item: "перчатки вора",
    super_chicken_item: "суперкура",
    dog_item: "собака",
    feed_item: "корм для кур",
    auto_feeder_item: "авто\nкормление",
    or_label: "ИЛИ",
    discount_label: "скидка 20%",
    withdraw_label: "вывести деньги\nна кошелек",
    max_btn: "MAX",
    add_feed_btn: "+",
    death_warning_2h: "⚠️ Осталось 2 часа до смерти курицы!",
    eggs_warning: "Яйца в лотке! Собери их скорее.",
    insufficient_balance: "Недостаточно монет!",
  },
  en: {
    feed_btn: "FEED",
    collect_btn: "Collect Eggs",
    market_title: "MARKET",
    leaders_title: "LEADERS",
    settings_title: "SETTINGS",
    day_label: "Day",
    no_feed_error: "No feed! Buy at market.",
    chicken_died_title: "Chicken died 😢",
    chicken_died_body: "Your chicken starved to death.\nEarned money is saved!",
    restart_btn: "Start Over",
    trader_title: "Trader arrived! 🎪",
    buy_chicken_discount: "Buy chicken with 20% discount",
    withdraw_money: "Withdraw money to wallet",
    no_glove_popup: "You don't have thief gloves. Buy them at market!",
    go_to_market: "To Market",
    dog_protection: "Dog guards this farm! 🐕 Can't steal anything.",
    already_stolen: "Eggs were already stolen today. Come back tomorrow!",
    tutorial_1: "Your chicken lays golden eggs! 🐔\nTo start, add feed to the feeder.",
    tutorial_2: "Great! Your chicken has food for 24 hours.\nYou need to add feed every day. More chickens = more food needed!",
    tutorial_3: "Watch your feed supply in the top corner. Buy feed at market or earn it for each invited friend. Bonus: each friend gives you 3 feed bags!",
    tutorial_4: "At the market you can buy feed, extra chickens or other upgrades for your farm.",
    tutorial_5: "You can steal eggs from other players! To protect yours — hire a guard dog at market. 🐕",
    tutorial_6: "Every 10 days a trader visits your farm. You can sell eggs and withdraw money! 💰",
    next_btn: "Next →",
    close_btn: "Close",
    got_it: "Got it!",
    days_until_trader: "Trader in {days} days",
    wallet_saved: "Wallet saved! ✓",
    no_wallet: "Link your TON wallet in settings to withdraw.",
    withdraw_pending: "Request accepted! Check status in history.",
    invite_msg: "My chicken lays golden eggs 🐔 Get yours! ",
    death_warning: "⚠️ 2 hours left! Feed your chicken!",
    low_feed_warning: "🛒 Only 1 feed bag left!",
    balance_label: "Balance",
    nickname_label: "Nickname",
    wallet_label: "TON Wallet Address",
    invite_label: "Invite a Friend",
    friends_count: "Invited friends:",
    withdraw_history: "WITHDRAWAL HISTORY",
    auth_label: "Authorization",
    lang_label: "lang",
    already_owned: "Owned ✓",
    buy_btn: "Buy",
    total_label: "Total:",
    pay_btn: "PAY",
    list_of_leaders: "LEADERBOARD",
    list_of_players: "PLAYERS LIST",
    score_label: "points",
    steal_btn: "Steal Eggs",
    chickens_label: "Chickens:",
    feed_bags_label: "Feed bags",
    yes_btn: "YES",
    no_btn: "NO",
    market_btn: "MARKET",
    ok_btn: "OK",
    chicken_item: "chicken",
    glove_item: "thief gloves",
    super_chicken_item: "super chicken",
    dog_item: "dog",
    feed_item: "chicken feed",
    auto_feeder_item: "auto\nfeeder",
    or_label: "OR",
    discount_label: "20% discount",
    withdraw_label: "withdraw money\nto wallet",
    max_btn: "MAX",
    add_feed_btn: "+",
    death_warning_2h: "⚠️ 2 hours until chicken dies!",
    eggs_warning: "Eggs in tray! Collect them fast.",
    insufficient_balance: "Insufficient balance!",
  },
};

// Add minimal stubs for other 8 languages (copy en as fallback, translators fill in)
["zh","hi","es","fr","ar","bn","pt","ur"].forEach(lang => {
  TRANSLATIONS[lang] = { ...TRANSLATIONS.en };
});

// Override specific zh phrases
Object.assign(TRANSLATIONS.zh, {
  feed_btn: "喂食", market_title: "市场", leaders_title: "排行榜",
  settings_title: "设置", day_label: "天", tutorial_1: "你的鸡下金蛋！🐔\n添加饲料开始游戏。",
  market_btn: "市场", list_of_leaders: "排行榜", or_label: "或",
});

Object.assign(TRANSLATIONS.es, {
  feed_btn: "ALIMENTAR", market_title: "MERCADO", leaders_title: "LÍDERES",
  settings_title: "AJUSTES", day_label: "Día", market_btn: "MERCADO",
  list_of_leaders: "TABLA DE LÍDERES", or_label: "O",
});

class I18n {
  constructor() {
    this.lang = this._detectLang();
  }

  _detectLang() {
    const saved = localStorage.getItem("gef_lang");
    if (saved && TRANSLATIONS[saved]) return saved;
    const browser = navigator.language?.split("-")[0]?.toLowerCase();
    return TRANSLATIONS[browser] ? browser : "en";
  }

  setLang(lang) {
    if (TRANSLATIONS[lang]) {
      this.lang = lang;
      localStorage.setItem("gef_lang", lang);
    }
  }

  t(key, vars = {}) {
    const dict = TRANSLATIONS[this.lang] || TRANSLATIONS.en;
    let str = dict[key] || TRANSLATIONS.en[key] || key;
    Object.entries(vars).forEach(([k, v]) => {
      str = str.replace(`{${k}}`, v);
    });
    return str;
  }
}

window.i18n = new I18n();
