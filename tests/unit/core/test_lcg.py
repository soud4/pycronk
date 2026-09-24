from hypothesis import given
from hypothesis import strategies as st

from pycronk.core.prng.lcg import INCREMENT, MODULUS, MULTIPLIER, Lcg32


def sequential(seed: int, n: int) -> list[int]:
    out, state = [], seed % MODULUS
    for _ in range(n):
        state = (MULTIPLIER * state + INCREMENT) % MODULUS
        out.append(state)
    return out


def test_keystream_matches_prototype(vectors):
    for case in vectors["cases"]:
        seed = vectors["kdf"][case["password_keystream"]]
        lcg = Lcg32(seed)
        states = lcg.next_states(40)
        assert (states % 64).tolist() == case["keystream_40"]
        assert lcg.state == case["lcg_state_after_40"]


@given(st.integers(min_value=0, max_value=2**64), st.integers(min_value=0, max_value=9000))
def test_jump_ahead_equals_sequential(seed, n):
    assert Lcg32(seed).next_states(n).tolist() == sequential(seed, n)


def test_continuation_across_calls():
    split = Lcg32(123)
    first = split.next_states(5000).tolist() + split.next_states(3).tolist()
    assert first == Lcg32(123).next_states(5003).tolist()


def test_zero_states_keeps_state():
    lcg = Lcg32(99)
    assert lcg.next_states(0).size == 0
    assert lcg.state == 99
