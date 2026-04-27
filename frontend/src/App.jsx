/**
 * 应用入口壳组件。
 *
 * Args:
 *     children: 当前应用挂载的根内容。
 *
 * Returns:
 *     提供统一根节点包装的 React 组件。
 */
export default function App({ children }) {
  return <div className="app-root">{children}</div>;
}
