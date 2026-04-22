export function onlyDigits(value) {
    return value.replace(/\D/g, "");
}

export function formatCpf(value) {
    let digits = onlyDigits(value).slice(0, 11);
    digits = digits.replace(/(\d{3})(\d)/, "$1.$2");
    digits = digits.replace(/(\d{3})(\d)/, "$1.$2");
    digits = digits.replace(/(\d{3})(\d{1,2})$/, "$1-$2");
    return digits;
}

export function formatCep(value) {
    let digits = onlyDigits(value).slice(0, 8);
    digits = digits.replace(/(\d{5})(\d)/, "$1-$2");
    return digits;
}
