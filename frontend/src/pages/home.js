import { useEffect, useState } from "react"
import { Container, Row, Col, Card, Button } from "react-bootstrap"
import { Mic, MicOff, MicNone, PanTool } from "@mui/icons-material"

import Footer from "../components/footer"
import socket from "../socket"


const Member = props => {
  const [color, setColor] = useState("dark")
  const [icon, setIcon] = useState(<MicNone />)

  const handleToggleMic = event => {
    socket.emit(
      ((props.children.status === "speaking") || (props.children.status === "pointed")) ? (
        "mute"
      ) : (
        "unmute"
      ),
      props.children.name
    )
  }

  useEffect(() => {
    switch (props.children.status) {
      case "speaking":
        setColor("success")
        setIcon(<Mic />)
        break

      case "pointed":
        setColor("dark")
        setIcon(<MicOff />)
        break

      case "raised":
        setColor("primary")
        setIcon(<PanTool />)
        break

      case "muted":
        setColor("danger")
        setIcon(<MicOff />)
        break

      default:
        setColor("secondary")
        break
    }
  }
  ,[props.children.status])

  return (
    <Card className="mb-1">
      <Card.Body className="d-flex p-0">
        <div className="flex-grow-1 my-auto ms-2">
          {props.children.name.replace("_", " ")}
        </div>
        <Button
          variant="light"
          onClick={handleToggleMic}
          className={`text-${color}`}
        >
          {icon}
        </Button>
      </Card.Body>
    </Card>
  )
}


const MemberList = props => {
  return (
    <Col md={3} className="pt-3">
      <h3>{props.title}</h3>
      {props.children.map(member => {
        return (
          <Member>
            {member}
          </Member>
        )
      })}
    </Col>
  )
}


const Home = props => {
  const [members, setMembers] = useState([])

  useEffect(() => {
    socket.on("member_io", data => {
      if (data.enter) {
        setMembers(old_members => {
          for (const member of old_members) {
            if (member.name === data.name) {
              return old_members
            }
          }

          const new_member = {
            name: data.name,
            can_self_unmute: false,
            raised: false,
            muted: true,
            status: undefined
          }

          return [...old_members, new_member]
        })
      }
      else {
        setMembers(old_members => {
          return old_members.filter(member => member.name !== data.name)
        })
      }
    })

    const events = ["raised", "muted", "can_self_unmute"]

    for (const event of events) {
      socket.on(event, data => {
        setMembers(old_members => {
          const new_members = old_members.slice()
          for (const member of new_members) {
            if (member.name === data.name) {
              member[event] = data[event]

              if (!member.raised && !member.muted) {
                member.status = "speaking"
              }
              if (!member.raised && member.muted && member.can_self_unmute) {
                member.status = "pointed"
              }
              if (member.raised && member.muted && !member.can_self_unmute) {
                member.status = "raised"
              }
              if (!member.raised && member.muted && !member.can_self_unmute) {
                member.status = "muted"
              }
            }
          }

          return new_members
        })
      })
    }
  }, [])

  return (
    <Container className="h-100 d-flex flex-column">
      <Row className="g-2">
        <MemberList title="Speaking">
          {members.filter(member => (member.status === "speaking"))}
        </MemberList>
        <MemberList title="Pointed">
          {members.filter(member => (member.status === "pointed"))}
        </MemberList>
        <MemberList title="Raised">
          {members.filter(member => (member.status === "raised"))}
        </MemberList>
        <MemberList title="Muted">
          {members.filter(member => ((member.status === "muted") || (member.status === undefined)))}
        </MemberList>
      </Row>
      <Footer />
    </Container>
  )
}


export default Home
