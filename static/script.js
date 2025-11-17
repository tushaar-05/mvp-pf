tailwind.config = {
  theme: {
    extend: {
      colors: {
        primary: "#2D5BFF",
        darkBlue: "#1E2A47",
        lightBlue: "#EDF3FF",
        accent: "#20C997",
        greyBg: "#F8F9FB",
        textGrey: "#4A4F59",
        heading: "#0F1115",
        serviceBg: "#F0F5FF",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      },
      boxShadow: {
        glass: "0 20px 45px rgba(17, 24, 39, 0.15)",
        card: "0 4px 20px rgba(45, 91, 255, 0.08)",
        cardHover: "0 12px 30px rgba(45, 91, 255, 0.15)",
      },
    },
  },
};


// Impact counters animation using GSAP + ScrollTrigger
document.addEventListener('DOMContentLoaded', () => {
  // Guard if GSAP isn't loaded
  if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;
  gsap.registerPlugin(ScrollTrigger);

  const counters = document.querySelectorAll('#counters .counter');
  if (!counters.length) return;

  counters.forEach((el, i) => {
    const raw = el.getAttribute('data-target') || el.textContent || '0';
    const isFloat = raw.indexOf('.') !== -1;
    const target = parseFloat(raw.toString().replace(/,/g, '')) || 0;

    const obj = { value: 0 };

    // animate parent card in with a subtle pop when it enters view
    const card = el.closest('.bg-white') || el.parentElement;
    gsap.fromTo(card, { y: 12, opacity: 0 }, {
      y: 0,
      opacity: 1,
      duration: 0.6,
      ease: 'power2.out',
      scrollTrigger: { trigger: card, start: 'top 95%', once: true },
      delay: i * 0.05,
    });

    gsap.to(obj, {
      value: target,
      duration: Math.min(2.5, Math.max(0.9, target / 5000)),
      ease: 'power1.out',
      scrollTrigger: {
        trigger: '#impact',
        start: 'top 80%',
        once: true,
      },
      onUpdate: () => {
        let v = isFloat ? obj.value.toFixed(1) : Math.floor(obj.value);
        if (!isFloat) v = new Intl.NumberFormat().format(v);
        el.textContent = v;
      },
      onComplete: () => {
        const final = isFloat ? target.toFixed(1) : new Intl.NumberFormat().format(target);
        el.textContent = final;
      },
    });
  });
});

