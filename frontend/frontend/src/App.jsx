import { useState } from "react";
import { createJob, subscribeToJob, uploadHeadshot } from "./api";
import "./App.css";

const STYLE_OPTIONS = [
  "professional",
  "bold",
  "cinematic",
  "minimal",
  "energetic",
];

export default function App() {
  const [title, setTitle] = useState("");
  const [style, setStyle] = useState("professional");
  const [file, setFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [job, setJob] = useState(null);
  const [thumbnails, setThumbnails] = useState([]);

  const handleFiles = (files) => {
    const image = files?.[0];
    if (image?.type.startsWith("image/")) {
      setFile(image);
      setError("");
    } else if (image) {
      setError("Choose an image file for your headshot.");
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!title.trim()) {
      setError("Please enter a video title.");
      return;
    }

    if (!file) {
      setError("Please choose a headshot image.");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      const uploadResult = await uploadHeadshot(file);
      const newJob = await createJob({
        prompt: title,
        headshot_url: uploadResult.url,
        style,
        num_thumbnails: 1,
      });

      setJob(newJob);
      setThumbnails([]);

      subscribeToJob(newJob.id, {
        onThumbnailReady: (payload) => {
          setThumbnails((current) => {
            const exists = current.some(
              (item) => item.thumbnail_id === payload.thumbnail_id
            );

            if (exists) {
              return current.map((item) =>
                item.thumbnail_id === payload.thumbnail_id ? payload : item
              );
            }

            return [...current, payload];
          });
        },
        onThumbnailFailed: (payload) => {
          setError(payload.error_message || "Thumbnail generation failed.");
        },
        onJobComplete: (payload) => {
          setJob((current) => ({
            ...(current || {}),
            status: payload.status,
          }));
        },
        onError: (event) => {
          setError(event?.message || "The job stream encountered an error.");
        },
      });
    } catch (err) {
      setError(err.message || "Something went wrong while creating the thumbnail job.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="studio-shell">
      <div className="ambient-glow" aria-hidden="true" />
      <nav className="topbar" aria-label="Main navigation">
        <a className="brand" href="#top" aria-label="Thumbnail AI home">
          <span className="brand-mark" aria-hidden="true">T</span>
          Thumbnail<span>AI</span>
        </a>
        <a className="dashboard-link" href="#preview">Dashboard <span aria-hidden="true">↗</span></a>
      </nav>

      <main id="top" className="studio-main">
        <section className="hero-copy" aria-labelledby="page-title">
          <div className="hero-kicker"><span className="sparkle" aria-hidden="true">✳</span> AI-POWERED CREATIVE STUDIO</div>
          <h1 id="page-title">Make them<br /><span>stop scrolling.</span></h1>
          <p>Turn your next big idea into a thumbnail worth clicking. Pick a look, add your headshot, and let AI do the heavy lifting.</p>
        </section>

        <section className="workspace" aria-label="Thumbnail generator">
          <form className="create-panel" onSubmit={handleSubmit}>
            <div className="section-heading">
              <div><span className="step-label">01 / YOUR CONCEPT</span><h2>Create a thumbnail</h2></div>
              <span className="live-indicator"><i /> READY</span>
            </div>

            <label className="field-label" htmlFor="video-title">What’s your video about?</label>
            <input
              id="video-title"
              className="title-input"
              type="text"
              placeholder="e.g. I spent 30 days in the world's quietest city"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              maxLength={180}
            />
            <div className="input-meta"><span>Give your idea a little context</span><span>{title.length}/180</span></div>

            <div className="field-label style-label">Choose a visual direction</div>
            <div className="style-picker" role="group" aria-label="Thumbnail style">
              {STYLE_OPTIONS.map((option) => (
                <button
                  className={`style-option${style === option ? " selected" : ""}`}
                  type="button"
                  key={option}
                  aria-pressed={style === option}
                  onClick={() => setStyle(option)}
                >
                  {option}
                </button>
              ))}
            </div>

            <label
              className={`upload-zone${isDragging ? " dragging" : ""}${file ? " has-file" : ""}`}
              htmlFor="headshot"
              onDragOver={(event) => { event.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={(event) => { event.preventDefault(); setIsDragging(false); handleFiles(event.dataTransfer.files); }}
            >
              <input id="headshot" type="file" accept="image/*" onChange={(event) => handleFiles(event.target.files)} />
              <span className="upload-icon" aria-hidden="true">{file ? "✓" : "↑"}</span>
              <span className="upload-title">{file ? file.name : "Add your headshot"}</span>
              <span className="upload-hint">{file ? "Click to choose a different image" : "Drop an image here or browse files"}</span>
            </label>

            {error ? <div className="error-box" role="alert">{error}</div> : null}

            <button className="generate-button" type="submit" disabled={isLoading}>
              <span>{isLoading ? "Creating your thumbnail..." : "Generate thumbnail"}</span>
              <span aria-hidden="true">{isLoading ? "···" : "↗"}</span>
            </button>
            <p className="privacy-note">Your image is only used to create your thumbnail.</p>
          </form>

          <aside id="preview" className="preview-panel">
            <div className="section-heading preview-heading">
              <div><span className="step-label">02 / THE RESULT</span><h2>Your preview</h2></div>
              {job ? <span className="job-status">{job.status || "pending"}</span> : null}
            </div>

            <div className={`preview-frame${thumbnails.length ? " has-result" : ""}`}>
              {thumbnails.length ? (
                <img src={thumbnails[0].imagekit_url} alt={thumbnails[0].style_name || "Generated YouTube thumbnail"} />
              ) : (
                <div className="preview-empty">
                  <span className="preview-orbit orbit-one" aria-hidden="true" />
                  <span className="preview-orbit orbit-two" aria-hidden="true" />
                  <span className="preview-stamp" aria-hidden="true">16:9</span>
                  <div className="preview-empty-copy">
                    <span className="preview-symbol" aria-hidden="true">✳</span>
                    <strong>{isLoading ? "Your idea is taking shape" : "Your next big click"}</strong>
                    <span>{isLoading ? "This can take a little moment" : "A fresh canvas, ready for your idea"}</span>
                  </div>
                </div>
              )}
            </div>

            <div className="preview-footer">
              <div><span className="result-dot" /><span>{thumbnails.length ? "Thumbnail generated" : "YOUTUBE THUMBNAIL"}</span></div>
              {thumbnails[0]?.imagekit_url ? <a href={thumbnails[0].imagekit_url} target="_blank" rel="noreferrer" download>Download <span aria-hidden="true">↓</span></a> : <span className="preview-format">1280 × 720</span>}
            </div>
          </aside>
        </section>
        <footer className="page-footer"><span>MADE FOR YOUR NEXT GOOD IDEA</span><span>THUMBNAIL AI <i>·</i> CREATIVE TOOLS</span></footer>
      </main>
    </div>
  );
}