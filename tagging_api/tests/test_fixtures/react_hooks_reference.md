# React Hooks Reference

A comprehensive reference for React Hooks API.

## useState

Declares state variable in functional components.

```jsx
const [state, setState] = useState(initialState);
```

**Example:**

```jsx
function Counter() {
  const [count, setCount] = useState(0);
  
  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>Increment</button>
    </div>
  );
}
```

## useEffect

Performs side effects in functional components. Runs after render.

```jsx
useEffect(() => {
  // Effect code
  return () => {
    // Cleanup (optional)
  };
}, [dependencies]);
```

**Example:**

```jsx
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  
  useEffect(() => {
    fetchUser(userId).then(setUser);
  }, [userId]);
  
  return <div>{user?.name}</div>;
}
```

## useContext

Consumes React Context without nesting.

```jsx
const value = useContext(MyContext);
```

## useReducer

Alternative to useState for complex state logic.

```jsx
const [state, dispatch] = useReducer(reducer, initialState);
```

**Example:**

```jsx
function reducer(state, action) {
  switch (action.type) {
    case 'increment':
      return { count: state.count + 1 };
    case 'decrement':
      return { count: state.count - 1 };
    default:
      throw new Error();
  }
}

function Counter() {
  const [state, dispatch] = useReducer(reducer, { count: 0 });
  
  return (
    <>
      Count: {state.count}
      <button onClick={() => dispatch({ type: 'increment' })}>+</button>
      <button onClick={() => dispatch({ type: 'decrement' })}>-</button>
    </>
  );
}
```

## useCallback

Memoizes callback functions.

```jsx
const memoizedCallback = useCallback(() => {
  doSomething(a, b);
}, [a, b]);
```

## useMemo

Memoizes expensive calculations.

```jsx
const memoizedValue = useMemo(() => computeExpensiveValue(a, b), [a, b]);
```

## useRef

Creates mutable reference that persists across renders.

```jsx
const refContainer = useRef(initialValue);
```

**Common uses:**
- Accessing DOM elements
- Storing mutable values
- Keeping previous values

## useImperativeHandle

Customizes instance value exposed to parent when using ref.

```jsx
useImperativeHandle(ref, () => ({
  focus: () => {
    inputRef.current.focus();
  }
}));
```

## useLayoutEffect

Similar to useEffect but fires synchronously after DOM mutations.

## useDebugValue

Displays label in React DevTools for custom hooks.

```jsx
useDebugValue(value);
```

## Rules of Hooks

1. Only call hooks at the top level
2. Only call hooks from React functions
3. Use ESLint plugin to enforce rules

## Custom Hooks

Create reusable stateful logic:

```jsx
function useWindowWidth() {
  const [width, setWidth] = useState(window.innerWidth);
  
  useEffect(() => {
    const handleResize = () => setWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  return width;
}
```
