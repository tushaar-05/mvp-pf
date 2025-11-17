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

document.addEventListener("DOMContentLoaded", () => {
  const serviceData = [
    {
      title: "Deep Cleaning",
      desc: "Industrial-grade disinfectants for homes, offices, and labs with detailed reporting.",
      price: "₹1,800",
      tag: "Sanitation",
      sla: "90 min",
      layout: "lg:col-span-2 lg:row-span-2",
      icon: '<path d="M16 20H32V36H16V20Z"/><path d="M20 16H28V20H20V16Z"/><path d="M14 24H12C9.79 24 8 25.79 8 28V36H16"/><path d="M34 24H36C38.21 24 40 25.79 40 28V36H32"/>',
    },
    {
      title: "Electrical Repairs",
      desc: "Licensed electricians for wiring, panels, diagnostics, and safety certifications.",
      price: "₹900",
      tag: "Power",
      sla: "45 min",
      layout: "lg:col-span-2",
      icon: '<path d="M24 8L16 24H24L20 40L32 20H24L28 8Z"/>',
    },
    {
      title: "AC Servicing",
      desc: "Split & window AC maintenance with gas checks and pressure balancing.",
      price: "₹1,200",
      tag: "Climate",
      sla: "75 min",
      layout: "",
      icon: '<rect x="14" y="14" width="20" height="12" rx="2"/><path d="M16 28H32"/><path d="M20 32L18 36"/><path d="M24 32V38"/><path d="M28 32L30 36"/>',
    },
    {
      title: "Carpentry",
      desc: "Precision carpenters for modular installations, furniture fixes, and fit-outs.",
      price: "₹1,100",
      tag: "Build",
      sla: "60 min",
      layout: "",
      icon: '<path d="M12 18L30 36L36 30L18 12L12 18Z"/><path d="M30 12L36 18"/><path d="M18 30L12 36"/>',
    },
    {
      title: "Plumbing",
      desc: "Leak fixes, fixture installs, and preventive pressure balancing.",
      price: "₹950",
      tag: "Water",
      sla: "50 min",
      layout: "lg:row-span-2",
      icon: '<path d="M18 12V20C18 22.21 19.79 24 22 24H26C28.21 24 30 25.79 30 28V36"/><path d="M30 12V20C30 22.21 28.21 24 26 24H22C19.79 24 18 25.79 18 28V36"/><path d="M14 36H34"/>',
    },
    {
      title: "Appliance Repair",
      desc: "Certified technicians for refrigerators, washers, ovens, and more.",
      price: "₹1,400",
      tag: "Appliances",
      sla: "80 min",
      layout: "",
      icon: '<rect x="16" y="10" width="16" height="28" rx="2"/><path d="M16 18H32"/>',
    },
    {
      title: "Painting & Finishing",
      desc: "Interior refresh with surface prep, masking, and VOC-safe materials.",
      price: "₹2,500",
      tag: "Finishing",
      sla: "120 min",
      layout: "lg:col-span-2",
      icon: '<rect x="12" y="14" width="24" height="10" rx="2"/><path d="M22 24V38H26V24"/>',
    },
    {
      title: "Pest Control",
      desc: "Safe termite, rodent, and vector elimination with warranty coverage.",
      price: "₹1,600",
      tag: "Safety",
      sla: "70 min",
      layout: "",
      icon: '<circle cx="24" cy="20" r="6"/><path d="M24 26V36"/><path d="M18 32H30"/><path d="M14 16L34 16"/><path d="M10 24H38"/>',
    },
    {
      title: "Home Sanitization",
      desc: "Medical-grade aerosol treatments for high-touch surfaces and HVAC.",
      price: "₹2,300",
      tag: "Hygiene",
      sla: "85 min",
      layout: "",
      icon: '<circle cx="18" cy="20" r="4"/><circle cx="30" cy="16" r="3"/><circle cx="30" cy="28" r="5"/><path d="M20 24L28 26"/>',
    },
    {
      title: "Delivery Assistance",
      desc: "On-demand helpers for moving, loading, and city-wide delivery support.",
      price: "₹800",
      tag: "Logistics",
      sla: "30 min",
      layout: "",
      icon: '<rect x="12" y="18" width="16" height="16" rx="2"/><path d="M28 24H36V34H24"/><circle cx="20" cy="34" r="4"/><circle cx="32" cy="34" r="4"/>',
    },
    {
      title: "IT & Network Setup",
      desc: "Secure router installs, cabling, CCTV, and small office network builds.",
      price: "₹1,500",
      tag: "Infra",
      sla: "65 min",
      layout: "",
      icon: '<rect x="14" y="20" width="20" height="10" rx="2"/><path d="M24 12V20"/><path d="M18 12H30"/>',
    },
    {
      title: "HVAC Installations",
      desc: "Commercial & residential ducting, balancing, and commissioning.",
      price: "₹3,200",
      tag: "HVAC",
      sla: "150 min",
      layout: "lg:col-span-2",
      icon: '<rect x="14" y="14" width="20" height="12" rx="2"/><path d="M18 28L16 34"/><path d="M24 28V36"/><path d="M30 28L32 34"/>',
    },
  ];
  const serviceGrid = document.getElementById("serviceGrid");
  const template = document.getElementById("serviceCardTemplate");
  serviceData.forEach((service) => {
    const cardFragment = template.content.cloneNode(true);
    const card = cardFragment.querySelector(".service-card");
    if (service.layout) {
      service.layout.split(" ").forEach((cls) => cls && card.classList.add(cls));
    }
    card.querySelector(".service-title").textContent = service.title;
    card.querySelector(".service-desc").textContent = service.desc;
    card.querySelector(".service-price").textContent = service.price;
    card.querySelector(".service-sla").textContent = service.sla;
    card.querySelector(".service-tag").textContent = service.tag;
    card.querySelector(".service-icon svg").innerHTML = service.icon;
    serviceGrid.appendChild(cardFragment);
  });

  const featureData = [
    { title: "Identity-verified workers", desc: "Every specialist is ID-verified, face-matched, and background screened through offline checks." },
    { title: "Transparent pricing", desc: "Live rates updated by city, slot, and complexity—no hidden charges on payout." },
    { title: "Live worker location tracking", desc: "Track arrival, job status, and wrap-up in real time with map-level accuracy." },
    { title: "Fast same-day availability", desc: "Match with ready professionals across all major pin codes within minutes." },
    { title: "Quality-controlled professionals", desc: "Performance scored after every job with retraining pathways and audits." },
    { title: "Secure payments", desc: "Funds are kept in escrow until you mark the job complete." },
  ];
  const features = document.getElementById("features");
  featureData.forEach((feature) => {
    const block = document.createElement("div");
    block.className = "bg-white rounded-2xl border border-black/5 p-8 space-y-4 feature-card";
    block.innerHTML = `
      <div class="w-10 h-10 rounded-lg border border-primary/30"></div>
      <h3 class="text-2xl font-semibold">${feature.title}</h3>
      <p class="text-textGrey">${feature.desc}</p>
    `;
    features.appendChild(block);
  });

  const faqData = [
    { q: "How do you vet professionals before onboarding?", a: "Our ops team verifies ID, police records, trade certifications, and conducts supervised trial jobs before enabling bookings." },
    { q: "Can I reschedule or cancel without penalties?", a: "Rescheduling is free until 3 hours before your slot. Cancellations within 2 hours may incur a nominal fee to compensate the professional." },
    { q: "What happens if a job takes longer than estimated?", a: "We update the scope transparently inside the app, including any revised pricing, which you must approve before work continues." },
    { q: "How do payouts work for workers?", a: "Workers receive instant payouts to their Fieldline wallet once the customer confirms completion. Withdrawals to bank accounts are available 24/7." },
    { q: "Is equipment or material included?", a: "Basic tools are always included. Specialized materials can be added at checkout or reimbursed at cost after uploading a bill." },
    { q: "Can businesses integrate Fieldline into internal CRMs?", a: "Our Business plan includes secure APIs and webhooks for job creation, tracking, and billing data syncing." },
    { q: "Do you operate outside metros?", a: "We're active in 28 cities with expansion routes planned every quarter. Join the waitlist inside the app for updates." },
    { q: "How do you ensure service quality?", a: "We review job recordings, follow-up surveys, and do random audits. Workers with low ratings enter coaching programs before relisting." },
    { q: "What support options are available?", a: "Customers and workers have access to live chat, phone escalation, and dedicated success managers on select plans." },
    { q: "Are there long-term contracts?", a: "No contracts. Scale up or pause anytime. Business plans can unlock SLA-backed commitments on request." },
  ];
  const faqList = document.getElementById("faqList");
  faqData.forEach((faq, index) => {
    const item = document.createElement("div");
    item.className = "bg-white rounded-2xl border border-black/5 p-6";
    item.innerHTML = `
      <button class="faq-toggle flex justify-between items-center w-full text-left text-lg font-semibold text-heading">
        <span>${faq.q}</span>
        <span class="text-primary text-2xl leading-none">+</span>
      </button>
      <div class="accordion-content max-h-0 transition-all duration-300 ease-linear">
        <p class="text-textGrey mt-4">${faq.a}</p>
      </div>
    `;
    faqList.appendChild(item);
  });

  document.getElementById("currentYear").textContent = new Date().getFullYear();

  const mobileToggle = document.getElementById("mobileToggle");
  const mobileMenu = document.getElementById("mobileMenu");
  let mobileOpen = false;
  mobileToggle.addEventListener("click", () => {
    mobileOpen = !mobileOpen;
    mobileMenu.style.transform = mobileOpen ? "scaleY(1)" : "scaleY(0)";
    mobileMenu.style.opacity = mobileOpen ? "1" : "0";
  });

  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", function (e) {
      const target = document.querySelector(this.getAttribute("href"));
      if (target) {
        e.preventDefault();
        window.scrollTo({
          top: target.offsetTop - 80,
          behavior: "smooth",
        });
        if (mobileOpen) {
          mobileToggle.click();
        }
      }
    });
  });

  const pricingToggle = document.querySelectorAll(".price");
  document.getElementById("monthlyBtn").addEventListener("click", () => {
    document.getElementById("monthlyBtn").classList.add("bg-white", "text-heading", "shadow");
    document.getElementById("yearlyBtn").classList.remove("bg-white", "text-heading", "shadow");
    document.getElementById("yearlyBtn").classList.add("text-textGrey");
    pricingToggle.forEach((el) => (el.textContent = `₹${el.dataset.monthly}`));
  });
  document.getElementById("yearlyBtn").addEventListener("click", () => {
    document.getElementById("yearlyBtn").classList.add("bg-white", "text-heading", "shadow");
    document.getElementById("monthlyBtn").classList.remove("bg-white", "text-heading", "shadow");
    document.getElementById("monthlyBtn").classList.add("text-textGrey");
    pricingToggle.forEach((el) => (el.textContent = `₹${el.dataset.yearly}`));
  });

  const faqToggles = document.querySelectorAll(".faq-toggle");
  faqToggles.forEach((toggle) => {
    toggle.addEventListener("click", () => {
      const content = toggle.nextElementSibling;
      const isOpen = content.style.maxHeight && content.style.maxHeight !== "0px";
      if (isOpen) {
        content.style.maxHeight = "0px";
        toggle.querySelector("span:last-child").textContent = "+";
      } else {
        content.style.maxHeight = content.scrollHeight + "px";
        toggle.querySelector("span:last-child").textContent = "–";
      }
    });
  });

  const testimonialTrack = document.getElementById("testimonialTrack");
  let testimonialIndex = 0;
  setInterval(() => {
    testimonialIndex = (testimonialIndex + 1) % 3;
    testimonialTrack.style.transform = `translateX(-${testimonialIndex * 100}%)`;
  }, 6000);

  gsap.registerPlugin(ScrollTrigger);

  gsap.from(".hero-copy > *", {
    opacity: 0,
    y: 30,
    duration: 1,
    stagger: 0.1,
  });

  gsap.from(".hero-search", {
    opacity: 0,
    y: 60,
    duration: 1,
    delay: 0.2,
  });

  gsap.utils.toArray(".service-card").forEach((card) => {
    card.addEventListener("mouseenter", () => {
      card.classList.add("shadow-cardHover");
      card.classList.remove("shadow-card");
    });
    card.addEventListener("mouseleave", () => {
      card.classList.remove("shadow-cardHover");
      card.classList.add("shadow-card");
    });
  });

  gsap.from(".service-card", {
    scrollTrigger: {
      trigger: "#serviceGrid",
      start: "top 80%"
    },
    y: 60,
    opacity: 0.3,
    duration: 0.8,
    ease: "power3.out",
  });

  gsap.from("#howSteps > div", {
    scrollTrigger: {
      trigger: "#howSteps",
      start: "top 70%",
    },
    x: 40,
    opacity: 0,
    stagger: 0.2,
    duration: 0.9,
  });

  gsap.from("#features > div", {
    scrollTrigger: {
      trigger: "#features",
      start: "top 70%",
    },
    opacity: 0,
    scale: 0.95,
    stagger: 0.15,
    duration: 0.9,
  });

  gsap.from("#customersColumn", {
    scrollTrigger: {
      trigger: "#customersColumn",
      start: "top 80%",
    },
    x: -80,
    opacity: 0,
    duration: 1,
  });
  gsap.from("#workersColumn", {
    scrollTrigger: {
      trigger: "#workersColumn",
      start: "top 80%",
    },
    x: 80,
    opacity: 0,
    duration: 1,
  });

  gsap.from("#phoneMockup", {
    scrollTrigger: {
      trigger: "#app",
      start: "top 70%",
    },
    opacity: 0,
    scale: 0.9,
    duration: 1,
  });

  gsap.from(".pricing-card", {
    scrollTrigger: {
      trigger: "#pricing",
      start: "top 80%",
    },
    y: 60,
    opacity: 0,
    stagger: 0.2,
    duration: 0.9,
  });

  gsap.utils.toArray(".counter").forEach((counter) => {
    const target = parseFloat(counter.dataset.target);
    gsap.fromTo(
      counter,
      { innerText: 0 },
      {
        innerText: target,
        scrollTrigger: {
          trigger: counter,
          start: "bottom 90%",
        },
        duration: 2,
        snap: { innerText: 1 },
        ease: "power1.out",
        modifiers: {
          innerText(value) {
            return Number(value).toFixed(target % 1 !== 0 ? 1 : 0);
          },
        },
      }
    );
  });

  gsap.to("#heroGraphic", {
    yPercent: -10,
    scrollTrigger: {
      trigger: "#heroGraphic",
      scrub: true,
    },
  });

  const parallaxEls = document.querySelectorAll("[data-parallax]");
  document.addEventListener("mousemove", (event) => {
    parallaxEls.forEach((el) => {
      const rect = el.getBoundingClientRect();
      const depth = parseFloat(el.dataset.parallax);
      const offsetX = ((event.clientX - rect.left) / rect.width - 0.5) * depth;
      const offsetY = ((event.clientY - rect.top) / rect.height - 0.5) * depth;
      el.style.transform = `translate(${offsetX}px, ${offsetY}px)`;
    });
  });

  gsap.to("#ctaMotion", {
    scale: 1.1,
    rotate: 8,
    scrollTrigger: {
      trigger: "#contact",
      start: "top bottom",
      scrub: true,
    },
    duration: 10,
    repeat: -1,
    yoyo: true,
  });
});