import React, { useState, useEffect } from 'react'
import ReactDOM from 'react-dom'

import Home from "./pages/home"
import Login from "./pages/login"

import socket from "./socket"

import "./static/style.css"


const App = props => {
  const [joinned, setJoinned] = useState(false)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    socket.on("connect", () => {
      setConnected(socket.connected)
    })
    socket.on("disconnect", () => {
      setConnected(socket.connected)
    })

    socket.on("joinned", data => {
      setJoinned(data)
    })
  }, [])

  return (
    (joinned && connected) ? (
      <Home />
    ) : (
      <Login />
    )
  )
}


ReactDOM.render(
  <App />,
  document.getElementById('root')
)
