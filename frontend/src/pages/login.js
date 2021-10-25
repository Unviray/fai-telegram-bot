import { useState, useEffect } from "react"
import { Container, Form, Button, Row, Col, Card } from "react-bootstrap"

import socket from "../socket"


const Login = props => {
  const [value, setValue] = useState("")
  const [joinning, setJoinning] = useState(false)
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

  useEffect(() => {
    let timeout = undefined

    if (joinning) {
      timeout = setTimeout(() => {
        setJoinning(false)
      }, 10000)
    }

    return () => {
      clearTimeout(timeout)
    }
  }, [joinning])

  const handleChange = event => {
    setValue(event.target.value)
  }
  const handleSubmit = event => {
    event.preventDefault()
    console.log(value)
    setJoinning(true)
    socket.emit("join", value)
  }

  return (
    <Container>
      <Row className="justify-content-center">
        <Col md={6}>
          <Form as={Card} className="mt-5">
            <Card.Header>
              <div>
                Backend:{" "}
                {connected ? (
                  <span className="text-success fw-bold">Connected</span>
                ) : (
                  <span className="text-danger fw-bold">Not connected</span>
                )}
              </div>
              <div>
                Group call:{" "}
                {joinned ? (
                  <span className="text-success fw-bold">Joinned</span>
                ) : (
                  <span className="text-danger fw-bold">Not joinned</span>
                )}
              </div>
            </Card.Header>
            <Card.Body>
              <Row className="g-1">
                <Col sm={9}>
                  <Form.Control type="number" placeholder="Group ID" value={value} onChange={handleChange} />
                </Col>
                <Col sm={3} className="d-flex">
                  <Button type="submit" onClick={handleSubmit} className="flex-fill" disabled={!connected}>
                    {joinning ? (
                      <div className="spinner-border spinner-border-sm" role="status">
                        <span className="visually-hidden">Loading...</span>
                      </div>
                    ) : (
                      "Join"
                    )}
                  </Button>
                </Col>
              </Row>
            </Card.Body>
          </Form>
        </Col>
      </Row>
    </Container>
  )
}


export default Login
