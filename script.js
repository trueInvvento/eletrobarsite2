const header = document.querySelector('.main-header');
const nav = document.querySelector('#main-nav');
const toggle = document.querySelector('.menu-toggle');
const quoteForm = document.querySelector('#quote-form');
const feedback = document.querySelector('#form-feedback');

function setHeaderState() {
  header.classList.toggle('is-scrolled', window.scrollY > 24);
}

setHeaderState();
window.addEventListener('scroll', setHeaderState, { passive: true });

toggle?.addEventListener('click', () => {
  const expanded = toggle.getAttribute('aria-expanded') === 'true';
  toggle.setAttribute('aria-expanded', String(!expanded));
  nav.classList.toggle('is-open', !expanded);
});

nav?.querySelectorAll('a').forEach((link) => {
  link.addEventListener('click', () => {
    nav.classList.remove('is-open');
    toggle?.setAttribute('aria-expanded', 'false');
  });
});

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add('is-visible');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.15 });

document.querySelectorAll('.reveal').forEach((el) => observer.observe(el));

function onlyDigits(value) {
  return value.replace(/\D/g, '');
}

function buildWhatsAppMessage(data) {
  const lines = [
    'Olá! Quero um orçamento para alugar a Eletrobar.',
    '',
    `Nome: ${data.get('nome')}`,
    `E-mail: ${data.get('email')}`,
    `Telefone: ${data.get('telefone')}`,
    `Tipo de evento: ${data.get('evento')}`,
  ];

  const message = data.get('mensagem')?.trim();
  if (message) lines.push(`Mensagem: ${message}`);
  return encodeURIComponent(lines.join('\n'));
}

quoteForm?.addEventListener('submit', (event) => {
  event.preventDefault();

  if (!quoteForm.checkValidity()) {
    feedback.textContent = 'Preencha os campos obrigatórios para solicitar o orçamento.';
    quoteForm.reportValidity();
    return;
  }

  const data = new FormData(quoteForm);
  const phoneDigits = onlyDigits(data.get('telefone') || '');

  if (phoneDigits.length < 10) {
    feedback.textContent = 'Informe um telefone válido com DDD.';
    quoteForm.querySelector('[name="telefone"]').focus();
    return;
  }

  feedback.textContent = 'Abrindo WhatsApp para envio do orçamento...';
  const message = buildWhatsAppMessage(data);
  window.open(`https://wa.me/5561993703294?text=${message}`, '_blank', 'noopener,noreferrer');
});
