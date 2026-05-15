const overlay = document.getElementById("perfil-overlay")
const btnAbrir = document.getElementById("btn-abrir-perfil")
const btnFechar = document.getElementById("perfil-close")

btnAbrir.addEventListener("click", () => {
    overlay.removeAttribute("hidden")
    carregarDados()
})

btnFechar.addEventListener("click", () => {
    overlay.setAttribute("hidden", "")
})

overlay.addEventListener("click", (event) => {
    if (event.target === overlay) {
        overlay.setAttribute("hidden", "")
    }
})

function carregarDados() {
    fetch("/perfil/dados")
    .then(response => response.json())
    .then(dados => {
        const iniciais = dados.name.split(" ").map(p => p[0]).join("").toUpperCase()

        document.getElementById("perfil-nome-display").textContent = dados.name
        document.getElementById("perfil-nome-valor").textContent = dados.name
        document.getElementById("perfil-email").textContent = dados.email
        document.getElementById("perfil-cpf").textContent = dados.cpf
        document.getElementById("perfil-cep").textContent = dados.cep
        document.getElementById("perfil-street").textContent = dados.street
        document.getElementById("perfil-neighborhood").textContent = dados.neighborhood
        document.getElementById("perfil-city-state").textContent = `${dados.city} - ${dados.state}`
        document.getElementById("input-nome").value = dados.name
        document.getElementById("perfil-avatar").textContent = iniciais
    })
}

document.querySelectorAll(".perfil-edit-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        const form = document.getElementById(btn.dataset.target)
        if (form.hasAttribute("hidden")) {
            form.removeAttribute("hidden")
        } else {
            form.setAttribute("hidden", "")
        }
    })
})
