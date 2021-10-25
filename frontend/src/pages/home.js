import { useEffect, useState } from "react"
import { Container, Row, Col, Card, Button } from "react-bootstrap"
import { Mic, MicOff, MicNone } from "@mui/icons-material"

import socket from "../socket"


const Member = props => {
  const handleToggleMic = event => {
    socket.emit(
      (props.statu === "speaking") ? "mute" : "unmute",
      props.children
    )
  }

  return (
    <Card className="mb-1">
      <Card.Body className={props.statu ? "" : "d-none"}>
        {props.statu}
      </Card.Body>
      <Card.Footer className="d-flex">
        <div className="flex-grow-1">
          {props.children}
        </div>
        <Button onClick={handleToggleMic} size="sm">
          {(props.statu === "speaking") ? (
            <MicOff />
          ) : (
            <Mic />
          )}
        </Button>
      </Card.Footer>
    </Card>
  )
}


const List = props => {
  return (
    <Col md={4} className="pt-3">
      {props.children}
    </Col>
  )
}


const SpeakingList = props => {
  return (
    <List>
      {props.children.map(member => {
        return (
          <Member statu={member.statu}>
            {member.name}
          </Member>
        )
      })}
    </List>
  )
}


const RaisedList = props => {
  return (
    <List>
      {props.children.map(member => {
        return (
          <Member statu={member.statu}>
            {member.name}
          </Member>
        )
      })}
    </List>
  )
}


const MemberList = props => {
  return (
    <List>
      {props.children.map(member => {
        return (
          <Member statu={member.statu}>
            {member.name}
          </Member>
        )
      })}
    </List>
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
            statu: undefined
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

    socket.on("raise_hand", data => {
      setMembers(old_members => {
        const new_members = old_members.slice()
        for (const member of new_members) {
          if (member.name === data.name) {
            if ((data.raise) && (member.statu === undefined)) {
              member.statu = "raised"
            }

            if ((!data.raise) && (member.statu === "raised")) {
              member.statu = undefined
            }
          }
        }

        return new_members
      })
    })

    socket.on("muted", data => {
      setMembers(old_members => {
        const new_members = old_members.slice()
        for (const member of new_members) {
          if (member.name === data.name) {
            if ((data.muted) && (member.statu === "speaking")) {
              member.statu = undefined
            }

            if ((!data.muted) && (member.statu === undefined)) {
              member.statu = "speaking"
            }
          }
        }

        return new_members
      })
    })
  }, [])

  return (
    <Container>
      <Row>
        <SpeakingList>
          {members.filter(member => (member.statu === "speaking"))}
        </SpeakingList>
        <RaisedList>
          {members.filter(member => (member.statu === "raised"))}
        </RaisedList>
        <MemberList>
          {members.filter(member => (member.statu === undefined))}
        </MemberList>
      </Row>
    </Container>
  )
}


export default Home
