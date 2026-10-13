// ===== إعدادات =====
// رابط الباك إند (نغيّره لاحقًا لما نشغّل Colab)
const API_URL = "http://localhost:8000/chat";

// ===== عناصر الصفحة =====
const chatArea = document.getElementById("chatArea");
const userInput = document.getElementById("userInput");
const sidebar = document.getElementById("sidebar");

// ===== القائمة الجانبية =====
function toggleMenu() {
  sidebar.classList.toggle("open");
}

// ===== محادثة جديدة =====
function newChat() {
  chatArea.innerHTML = `
    <div class="message ai-message">
      <span class="avatar">🤖</span>
      <div class="bubble">مرحبا! أنا TRL-AI. كيف أقدر أساعدك اليوم؟</div>
    </div>
  `;
  if (sidebar.classList.contains("open")) {
    sidebar.classList.remove("open");
  }
}

// ===== إرفاق ملف =====
function attachFile() {
  // مؤقتًا: رسالة تنبيه
  alert("ميزة إرفاق الملفات - قريبًا!");
}

// ===== إضافة رسالة =====
function addMessage(text, sender) {
  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${sender}-message`;

  const avatar = document.createElement("span");
  avatar.className = "avatar";
  avatar.textContent = sender === "ai" ? "🤖" : "👤";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  messageDiv.appendChild(avatar);
  messageDiv.appendChild(bubble);
  chatArea.appendChild(messageDiv);

  // ننزل لآخر رسالة
  chatArea.scrollTop = chatArea.scrollHeight;

  return messageDiv;
}

// ===== إضافة أزرار التقييم =====
function addRatingBar(messageDiv, interactionId) {
  const ratingBar = document.createElement("div");
  ratingBar.className = "rating-bar";

  const likeBtn = document.createElement("button");
  likeBtn.className = "rate-btn";
  likeBtn.textContent = "👍";
  likeBtn.onclick = () => rateInteraction(interactionId, 1, likeBtn, dislikeBtn);

  const dislikeBtn = document.createElement("button");
  dislikeBtn.className = "rate-btn";
  dislikeBtn.textContent = "👎";
  dislikeBtn.onclick = () => rateInteraction(interactionId, -1, dislikeBtn, likeBtn);

  const correctBtn = document.createElement("button");
  correctBtn.className = "rate-btn";
  correctBtn.textContent = "✏️ صحّح";
  correctBtn.onclick = () => correctInteraction(interactionId);

  ratingBar.appendChild(likeBtn);
  ratingBar.appendChild(dislikeBtn);
  ratingBar.appendChild(correctBtn);

  messageDiv.appendChild(ratingBar);
}

// ===== إرسال رسالة =====
async function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;

  // نضيف رسالة المستخدم
  addMessage(text, "user");
  userInput.value = "";

  // رسالة "جاري الكتابة"
  const loadingDiv = addMessage("يكتب...", "ai");

  try {
    // نتصل بالباك إند
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });

    if (!response.ok) throw new Error("فشل الاتصال بالسيرفر");

    const data = await response.json();

    // نستبدل "يكتب..." بالرد الفعلي
    loadingDiv.querySelector(".bubble").textContent = data.reply;

    // نضيف أزرار التقييم
    addRatingBar(loadingDiv, data.interaction_id);

  } catch (error) {
    loadingDiv.querySelector(".bubble").textContent =
      "⚠️ تعذر الاتصال بالخادم. تأكد أن الباك إند شغال.";
    console.error(error);
  }
}

// ===== تقييم =====
async function rateInteraction(interactionId, rating, activeBtn, otherBtn) {
  // نبدل حالة الأزرار
  activeBtn.classList.add("active");
  otherBtn.classList.remove("active");

  try {
    await fetch(`${API_URL}/rate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        interaction_id: interactionId,
        rating: rating
      })
    });
  } catch (error) {
    console.error("فشل إرسال التقييم:", error);
  }
}

// ===== تصحيح =====
async function correctInteraction(interactionId) {
  const correction = prompt("اكتب الجواب الصحيح:");
  if (!correction) return;

  try {
    const response = await fetch(`${API_URL}/correct`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        interaction_id: interactionId,
        correction: correction
      })
    });

    if (response.ok) {
      alert("✅ تم حفظ التصحيح. شكرًا!");
    }
  } catch (error) {
    console.error("فشل إرسال التصحيح:", error);
  }
}