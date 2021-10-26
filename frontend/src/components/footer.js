import { useEffect, useState } from "react"

import { Mic, MicOff, MicNone, PanTool } from "@mui/icons-material"
import { Row, Col, Button } from "react-bootstrap"

import socket from "../socket"


const Footer = props => {
  const [mic, setMic] = useState(false)

  useEffect(() => {
    socket.on("my_mic", data => {
      setMic(data)
    })
  }, [])

  const handleClick = event => {
    socket.emit("mic", !mic)
  }

  return (
    <Row className="justify-content-center position-sticky mt-auto mb-3" style={{ bottom: "0px" }}>
      <Col md={4} className="d-flex justify-content-center">
        <Button variant={mic ? "success" : "primary"} onClick={handleClick} className="p-4 rounded-circle">
          {mic ? (
            <Mic style={{ fontSize: "3em" }} />
          ) : (
            <MicOff style={{ fontSize: "3em" }} />
          )}
        </Button>
      </Col>
    </Row>
  )
}


export default Footer
