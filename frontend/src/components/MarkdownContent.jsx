import DOMPurify from "dompurify";
import { marked, Renderer } from "marked";

const markdownRenderer = new Renderer();
markdownRenderer.html = () => "";

export default function MarkdownContent({ children = "" }) {
  const html = marked.parse(children, {
    breaks: true,
    gfm: true,
    renderer: markdownRenderer,
  });
  const safeHtml = DOMPurify.sanitize(html);

  return <div dangerouslySetInnerHTML={{ __html: safeHtml }} />;
}