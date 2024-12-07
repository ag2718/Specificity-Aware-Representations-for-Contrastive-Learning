from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
import torch

def calculate_metrics(predictions, labels, average='macro'):
    """
    Calculates precision, recall, and F1-score.
    """
    predictions = predictions.cpu().numpy()
    labels = labels.cpu().numpy()

    precision = precision_score(labels, predictions, average=average, zero_division=0)
    recall = recall_score(labels, predictions, average=average, zero_division=0)
    f1 = f1_score(labels, predictions, average=average, zero_division=0)

    return precision, recall, f1

def evaluate_model(model, dataloader, loss_fn, device, num_classes, class_tree, clf_classes, clf_class_to_id):
    """
    Evaluates the model on a given dataloader and returns classification statistics.
    """
    model.eval()  # Set model to evaluation mode
    running_loss = 0.0
    total_correct = 0
    total_samples = 0
    num_batches = 0

    all_predictions = []
    all_labels = []

    with torch.no_grad():  # Disable gradients for evaluation
        for images, labels in dataloader:
            images, labels = images.to(device), labels.to(device)

            labels = torch.tensor([class_tree.which_ancestor(label.item(), clf_classes) for label in labels], device='cuda')
            labels = torch.tensor([clf_class_to_id[clf_label.item()] for clf_label in labels], device='cuda')

            # Forward pass
            _, logits = model(images)
            loss = loss_fn(logits, labels)

            # Update loss
            running_loss += loss.item()

            # Predictions and accuracy
            _, predictions = torch.max(logits, dim=1)
            total_correct += (predictions == labels).sum().item()
            total_samples += labels.size(0)

            # Store predictions and labels for metric computation
            all_predictions.append(predictions)
            all_labels.append(labels)
            num_batches += 1

    # Combine all predictions and labels across batches
    all_predictions = torch.cat(all_predictions, dim=0)
    all_labels = torch.cat(all_labels, dim=0)

    # Compute metrics
    precision, recall, f1 = calculate_metrics(all_predictions, all_labels)
    conf_matrix = confusion_matrix(all_labels.cpu().numpy(), all_predictions.cpu().numpy())

    # Compute average loss and accuracy
    avg_loss = running_loss / num_batches
    accuracy = total_correct / total_samples

    return avg_loss, accuracy, precision, recall, f1, conf_matrix