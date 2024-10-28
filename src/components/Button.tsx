interface ButtonProps {
  id: string;
  text: string;
  handleClick: () => void;
}

const Button: React.FC<ButtonProps> = ({ id, text, handleClick }) => {
  return (
    <button
      className="btn btn-primary"
      type="button"
      id={id}
      onClick={handleClick}
    >
      {text}
    </button>
  );
};

export default Button;
