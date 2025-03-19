interface ButtonProps {
  id: string;
  text: string;
  handleClick: () => void;
  className?: string; // Optional className prop
}

const Button: React.FC<ButtonProps> = ({
  id,
  text,
  handleClick,
  className,
}) => {
  return (
    <button
      className={className ?? "btn btn-primary"}
      type="button"
      id={id}
      onClick={handleClick}
    >
      {text}
    </button>
  );
};

export default Button;
