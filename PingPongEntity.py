import netsquid as ns
import pydynaa as pd
ns.set_random_state(seed=42)


class PingEntity(pd.Entity):
    ping_event_type = pd.EventType("PING EVENT", "This is a ping event")
    delay = 10
    qubit = None

    def start(self, qubit):
        self.qubit = qubit
        self._schedule_now(PingEntity.ping_event_type)
        

    def wait_for_pong(self, pong_entity):
        pong_handler = pd.EventHandler(self._handle_pong_event)
        self._wait(pong_handler, entity=pong_entity,
                   event_type=PongEntity.pong_event_type)

    def _handle_pong_event(self, event):
        m, prob = ns.qubits.measure(self.qubit, observable=ns.Z)
        label = ["0", "1"]
        print(f"{ns.sim_time()}: Pong Event, PingEntity measured {label[m]}"
              f" with prob {prob}")
        self._schedule_after(self.delay, PingEntity.ping_event_type)


class PongEntity(pd.Entity):
    pong_event_type = pd.EventType("PONG EVENT", "This is a pong event")
    delay = 10

    def wait_for_ping(self, ping_entity):
        ping_handler = pd.EventHandler(self._handle_ping_event)
        self._wait(ping_handler, entity=ping_entity,
                   event_type=PingEntity.ping_event_type)

    def _handle_ping_event(self, event):
        print(event.source)
        m, prob = ns.qubits.measure(event.source.qubit, observable=ns.X)
        label = ["+", "-"]
        print(f"{ns.sim_time()}: Ping Event, PongEntity measured {label[m]}"
              f" with prob {prob}")
        self._schedule_after(self.delay, PongEntity.pong_event_type)


ping = PingEntity()
pong = PongEntity()

ping.wait_for_pong(pong)
pong.wait_for_ping(ping)

q, = ns.qubits.create_qubits(1)
ping.start(q)

stat = ns.sim_run(end_time=91)

