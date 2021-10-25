import axios from "axios"


const instance = axios.create({
  baseURL: "http://localhost:8080/"
})


export const GET = (url, data, callback) => {
  instance.get(url, { params: data })
    .then(callback)
    .catch((error) => { console.warn(error) })
}

export const POST = (url, data, callback) => {
  instance.post(url, data)
    .then(callback)
    .catch((error) => { console.warn(error) })
}
