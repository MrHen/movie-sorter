// LIST COMPARISON
titles_a = []
headers = document.querySelectorAll(".headline-2.prettify")
for (let header of headers) {
    titles_a.push(header.textContent)
}
JSON.stringify(titles_a)

titles_a = JSON.parse()

titles_b = []
headers = document.querySelectorAll(".headline-2.prettify")
for (let header of headers) {
    if (titles_a.includes(header.textContent)) {
    } else {
        header.style = "background-color: #434393;"
    }
}


// FILM LIST COMPARISON
titles_a = []
headers = document.querySelectorAll(".listitem .poster")
for (let header of headers) {
    titles_a.push(header.attributes["data-film-id"].textContent)
}
JSON.stringify(titles_a)

titles_a = JSON.parse()

headers = document.querySelectorAll(".listitem .poster")
for (let header of headers) {
    if (titles_a.includes(header.attributes["data-film-id"].textContent)) {
        header.style = "opacity: 0.1;"
    }
}

