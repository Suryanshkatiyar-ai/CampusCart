
document.addEventListener("DOMContentLoaded", () => {

    // Enable scroll animations
    document.documentElement.classList.add("js-ready");

    const revealElements = document.querySelectorAll(".reveal");

    // Animate elements when they enter the screen
    if ("IntersectionObserver" in window) {

        const observer = new IntersectionObserver(
            (entries, currentObserver) => {

                entries.forEach(entry => {

                    if (entry.isIntersecting) {

                        entry.target.classList.add("is-visible");

                        currentObserver.unobserve(entry.target);
                    }

                });

            },
            {
                threshold: 0.12,
                rootMargin: "0px 0px -40px 0px"
            }
        );

        revealElements.forEach(element => {
            observer.observe(element);
        });

    } else {

        revealElements.forEach(element => {
            element.classList.add("is-visible");
        });

    }


    // Glass navbar changes on scroll
    const header = document.querySelector(".site-header");

    function updateHeader() {

        if (window.scrollY > 40) {
            header.classList.add("scrolled");
        } else {
            header.classList.remove("scrolled");
        }

    }

    window.addEventListener("scroll", updateHeader, {
        passive: true
    });

    updateHeader();


    // 3D mouse movement on product cards
    const cards = document.querySelectorAll(".product-card");

    if (window.matchMedia("(pointer: fine)").matches) {

        cards.forEach(card => {

            card.addEventListener("pointermove", event => {

                const rect = card.getBoundingClientRect();

                const x = event.clientX - rect.left;
                const y = event.clientY - rect.top;

                const rotateX = ((y / rect.height) - 0.5) * -7;
                const rotateY = ((x / rect.width) - 0.5) * 7;

                card.style.setProperty("--rx", `${rotateX}deg`);
                card.style.setProperty("--ry", `${rotateY}deg`);

            });

            card.addEventListener("pointerleave", () => {

                card.style.setProperty("--rx", "0deg");
                card.style.setProperty("--ry", "0deg");

            });

        });

    }


    // Automatically make Borrow listings free
    const listingType = document.querySelector("#listing-type");
    const listingPrice = document.querySelector("#listing-price");
    const priceHint = document.querySelector("#price-hint");

    if (listingType && listingPrice) {

        function updateListingPrice() {

            if (listingType.value === "BORROW") {

                listingPrice.value = "0";
                listingPrice.disabled = true;
                listingPrice.required = false;

                priceHint.textContent =
                    "Borrow listings are free. No charge will be applied.";

            } else {

                listingPrice.disabled = false;
                listingPrice.required = true;
                listingPrice.value = "";

                priceHint.textContent =
                    "Enter your selling price or rental charge.";

            }

        }

        listingType.addEventListener("change", updateListingPrice);

        updateListingPrice();
    }

    console.log("CampusCart animations initialized!");

});
