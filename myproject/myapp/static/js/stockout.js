document.addEventListener("DOMContentLoaded", function() {
    const productSelect = document.getElementById("product-select");
    const unitInput = document.getElementById("unit-select");
    const stockDisplay = document.getElementById("available-stock");

    // Products data from Django template
    const products = JSON.parse(document.getElementById("products-data").textContent);

    productSelect.addEventListener("change", function() {
        const productId = productSelect.value;

        if (productId && products[productId]) {
            const p = products[productId];
            unitInput.value = p.unit_type;
            stockDisplay.textContent = `Available - Unit: ${p.quantity_unit}, Meters: ${p.quantity_meters}, KLG: ${p.quantity_klg}`;
        } else {
            unitInput.value = "";
            stockDisplay.textContent = "Available: -";
        }
    });
});