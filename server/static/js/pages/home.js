function toggleBalance() {
    const selector = document.getElementById("account-selector");
    const divCorrente = document.getElementById("balance-corrente");
    const divPoupanca = document.getElementById("balance-poupanca");
    const isPoupanca = selector.value === "poupanca";
    divCorrente.style.display = isPoupanca ? "none" : "block";
    divPoupanca.style.display = isPoupanca ? "block" : "none";
    localStorage.setItem("conta_selecionada", selector.value);
}

function abrirSeletorConta() {
    document.getElementById("card-poupanca").style.display = "none";
    document.getElementById("seletor-conta").style.display = "block";
    localStorage.setItem("poupanca_aberta", "true");
}

function toggleConta() {
    const selector = document.getElementById("account-selector");
    const label = document.getElementById("toggle-label");
    const novoValor = selector.value === "corrente" ? "poupanca" : "corrente";
    selector.value = novoValor;
    label.textContent = novoValor === "corrente" ? "Conta Corrente" : "Conta Poupança";
    localStorage.setItem("conta_selecionada", novoValor);
    toggleBalance();
}

document.addEventListener("DOMContentLoaded", () => {
    const poupancaAberta = localStorage.getItem("poupanca_aberta") === "true";
    const contaSelecionada = localStorage.getItem("conta_selecionada") || "corrente";

    if (poupancaAberta) {
        document.getElementById("card-poupanca").style.display = "none";
        document.getElementById("seletor-conta").style.display = "block";
        const selector = document.getElementById("account-selector");
        const label = document.getElementById("toggle-label");
        if (selector) {
            selector.value = contaSelecionada;
            label.textContent = contaSelecionada === "corrente" ? "Conta Corrente" : "Conta Poupança";
            toggleBalance();
        }
    }

    document.getElementById("btn-toggle-conta")?.addEventListener("click", toggleConta);
    document.getElementById("card-poupanca")?.addEventListener("click", abrirSeletorConta);
});
