const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); }
let catalog = [];
let selectedProduct = null;
const $ = id => document.getElementById(id);
function showScreen(which) {
  $("home").classList.toggle("hidden", which !== "home");
  $("order").classList.toggle("hidden", which !== "order");
  if (which === "order") loadCatalog();
}
function formatPLN(value) { return Number(value).toLocaleString("pl-PL",{style:"currency",currency:"PLN"}); }
async function loadCatalog() {
  try {
    const res = await fetch("/api/catalog");
    const data = await res.json();
    catalog = data.products || [];
    const holder = $("products");
    if (!catalog.length) { holder.innerHTML = '<p class="muted">Katalog jest jeszcze pusty. Administrator uzupełni go w bocie Telegram.</p>'; return; }
    holder.innerHTML = catalog.map(p => `<label class="product"><input type="radio" name="product" value="${p.id}"><span>${escapeHtml(p.name)}</span><strong>${p.price_label}</strong></label>`).join("");
    holder.querySelectorAll('input[name="product"]').forEach(el => el.addEventListener("change", () => { selectedProduct = catalog.find(p => p.id === Number(el.value)); updateTotal(); }));
    updateTotal();
  } catch(e) { $("products").innerHTML = '<p class="muted">Nie udało się pobrać katalogu. Spróbuj ponownie.</p>'; }
}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
function updateTotal(){
  const qty = Math.max(1,Math.min(99,Number($("quantity").value)||1));
  $("total").textContent = selectedProduct ? formatPLN(selectedProduct.price*qty) : "—";
}
$("quantity").addEventListener("input",updateTotal);
$("submit").addEventListener("click", async () => {
  const feedback = $("feedback"); feedback.className="feedback"; feedback.textContent="";
  if (!tg?.initData) { feedback.classList.add("error"); feedback.textContent="Otwórz tę aplikację przyciskiem w bocie Telegram, a nie bezpośrednio w przeglądarce."; return; }
  if (!selectedProduct) { feedback.classList.add("error"); feedback.textContent="Wybierz produkt."; return; }
  const payload = {
    product_id:selectedProduct.id, quantity:Number($("quantity").value),
    region:$("region").value, city:$("city").value.trim(), service:$("service").value,
    contact:$("contact").value.trim(), note:$("note").value.trim()
  };
  if (!payload.city || !payload.service || !payload.contact) { feedback.classList.add("error"); feedback.textContent="Uzupełnij miasto, usługę i kontakt."; return; }
  $("submit").disabled=true; $("submit").textContent="WYSYŁANIE…";
  try {
    const res=await fetch("/api/order",{method:"POST",headers:{"Content-Type":"application/json","X-Telegram-Init-Data":tg.initData},body:JSON.stringify(payload)});
    const data=await res.json();
    if(!res.ok) throw new Error(data.detail||"Nie udało się wysłać zgłoszenia.");
    feedback.classList.add("ok"); feedback.textContent=data.message||"Zgłoszenie wysłane.";
    tg.showAlert?.(feedback.textContent);
  } catch(e) { feedback.classList.add("error"); feedback.textContent=e.message; }
  finally { $("submit").disabled=false; $("submit").innerHTML='WYŚLIJ ZGŁOSZENIE <span>→</span>'; }
});
